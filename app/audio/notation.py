from __future__ import annotations
import os
import subprocess
from typing import List
from music21 import stream, note, meter, key as m21key, tempo as m21tempo, duration
from app.settings import settings

def f0_to_midi(f0_hz: List[float]) -> List[int]:
    import librosa, numpy as np
    midi = librosa.hz_to_midi(np.maximum(1e-6, f0_hz))
    midi = np.where(np.isfinite(midi), midi, 0.0)
    midi = np.clip(midi, 0, 127)
    return midi.astype(int).tolist()

def build_score(midi_pitches, onset_beats, dur_beats, key_signature, time_signature, qpm) -> stream.Score:
    sc = stream.Score()
    part = stream.Part()
    part.append(m21tempo.MetronomeMark(number=qpm))
    part.append(meter.TimeSignature(time_signature))
    try:
        part.append(m21key.Key(key_signature))
    except Exception:
        pass
    for mp, ob, db in zip(midi_pitches, onset_beats, dur_beats):
        if mp <= 0 or db <= 0:
            n = note.Rest()
        else:
            n = note.Note(mp)
        d = duration.Duration(quarterLength=db)
        n.duration = d
        part.append(n)
    sc.insert(0, part)
    return sc

def export_musicxml(score: stream.Score, out_path: str) -> str:
    score.write("musicxml", fp=out_path)
    return out_path

def render_to_pdf_png(musicxml_path: str, out_pdf: str | None, out_png: str | None) -> list[str]:
    out = []
    if settings.renderer == "mscore":
        for b in ["mscore", "musescore3", "musescore4"]:
            try:
                if out_pdf:
                    subprocess.run([b, "-o", out_pdf, musicxml_path], check=True, timeout=settings.render_timeout_sec)
                    out.append(out_pdf)
                if out_png:
                    subprocess.run([b, "-o", out_png, musicxml_path], check=True, timeout=settings.render_timeout_sec)
                    out.append(out_png)
                return out
            except Exception:
                continue
    elif settings.renderer == "verovio":
        if out_png:
            try:
                subprocess.run(["verovio", "--format", "png", "--output", out_png, musicxml_path],
                               check=True, timeout=settings.render_timeout_sec)
                out.append(out_png)
            except Exception:
                pass
    return out
