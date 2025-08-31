from __future__ import annotations
import os
from datetime import datetime
from celery import Celery
import numpy as np
import soundfile as sf
from app.settings import settings
from app.db.repository import update_job_status, add_artifact
from app.audio.io import load_audio_to_mono, validate_audio
from app.audio import preprocess as pp
from app.audio.f0 import estimate_f0_torchcrepe, estimate_f0_pyin
from app.audio.quantize import estimate_tempo, times_to_beats, quantize_beats
from app.audio.key_tempo import detect_key_from_pitches, default_time_signature
from app.audio.notation import f0_to_midi, build_score, export_musicxml, render_to_pdf_png
from app.audio.synthesis import synth_sine
from app.audio.separation import separate_vocals_demucs

celery_app = Celery("melody2score", broker=settings.redis_url, backend=settings.redis_url)

@celery_app.task(name="transcribe_job")
def transcribe_job(job_id: int, audio_path: str, params: dict) -> dict:
    update_job_status(job_id, status="running", progress=5)
    validate_audio(audio_path, settings.max_duration_sec, settings.max_file_mb)

    # optional separation
    if params.get("separation", "none") == "demucs":
        try:
            sep_path = separate_vocals_demucs(audio_path, os.path.join(settings.storage_dir, f"job_{job_id}", "separation"))
            src_path = sep_path
        except Exception:
            src_path = audio_path
    else:
        src_path = audio_path

    y, sr = load_audio_to_mono(src_path, settings.default_sr)

    if params.get("highpass", True):
        y = pp.highpass(y, sr)
    if params.get("denoise", True):
        y = pp.spectral_denoise(y, sr)
    if params.get("trim", True):
        y = pp.trim_silence(y)
    if params.get("normalize", True):
        y = pp.normalize(y)

    update_job_status(job_id, progress=25)

    backend = params.get("f0_backend", "torchcrepe")
    if backend == "pyin":
        t, f0_hz, voiced = estimate_f0_pyin(y, sr)
    else:
        t, f0_hz, voiced = estimate_f0_torchcrepe(y, sr)

    update_job_status(job_id, progress=45)

    qpm = float(params.get("tempo_qpm") or estimate_tempo(y, sr))
    beats = times_to_beats(t, qpm)
    onsets_beats = quantize_beats(beats, grid=0.25).tolist()
    dur_beats = np.diff(onsets_beats + [onsets_beats[-1] + 0.25]).tolist()

    midi = f0_to_midi(f0_hz.tolist())
    midi_key = detect_key_from_pitches([m for m in midi if m > 0]) if params.get("auto_key", True) else "C"

    update_job_status(job_id, progress=65)

    ts = params.get("time_signature", default_time_signature())
    score = build_score(midi, onsets_beats, dur_beats, key_signature=midi_key, time_signature=ts, qpm=qpm)

    job_dir = os.path.join(settings.storage_dir, f"job_{job_id}")
    os.makedirs(job_dir, exist_ok=True)
    musicxml_path = os.path.join(job_dir, "score.musicxml")
    export_musicxml(score, musicxml_path)
    add_artifact(job_id, "musicxml", musicxml_path)

    update_job_status(job_id, progress=80)

    y_synth = synth_sine(midi, onsets_beats, dur_beats, qpm, sr=sr)
    preview_path = os.path.join(job_dir, "preview.wav")
    sf.write(preview_path, y_synth, sr)
    add_artifact(job_id, "audio_preview", preview_path)

    pdf_path = os.path.join(job_dir, "score.pdf")
    png_path = os.path.join(job_dir, "score.png")
    outputs = render_to_pdf_png(musicxml_path, pdf_path, png_path)
    for p in outputs:
        kind = "pdf" if p.endswith(".pdf") else "png"
        add_artifact(job_id, kind, p)

    update_job_status(job_id, status="done", progress=100, finished_at=datetime.utcnow())
    return {"job_id": job_id, "artifacts": [musicxml_path, preview_path] + outputs}
