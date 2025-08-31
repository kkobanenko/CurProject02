from __future__ import annotations
import os
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from celery import Celery, Task
from celery.utils.log import get_task_logger
import numpy as np
import soundfile as sf

from app.settings import settings
from app.db.repository import (
    update_job_status, add_artifact, add_log, get_job, get_artifact_by_kind
)
from app.audio.io import load_audio_to_mono, validate_audio, get_audio_info
from app.audio import preprocess as pp
from app.audio.f0 import estimate_f0
from app.audio.quantize import estimate_tempo, quantize_rhythm
from app.audio.key_tempo import detect_key_from_pitches, default_time_signature
from app.audio.notation import f0_to_midi, build_score, export_musicxml, render_to_pdf_png
from app.audio.synthesis import synth_audio
from app.audio.separation import separate_sources

# Configure Celery
celery_app = Celery(
    "melody2score",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=['app.tasks.celery_tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

logger = get_task_logger(__name__)

class BaseTask(Task):
    """Base task class with error handling and logging."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        job_id = args[0] if args else None
        if job_id:
            error_msg = f"Task failed: {exc}\n{traceback.format_exc()}"
            update_job_status(job_id, status="failed", error=error_msg)
            add_log(job_id, "ERROR", error_msg)
        logger.error(f"Task {task_id} failed: {exc}")
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry."""
        job_id = args[0] if args else None
        if job_id:
            retry_msg = f"Task retrying: {exc}"
            add_log(job_id, "WARNING", retry_msg)
        logger.warning(f"Task {task_id} retrying: {exc}")

@celery_app.task(name="transcribe_job", base=BaseTask, bind=True)
def transcribe_job(self, job_id: int, audio_path: str, params: dict) -> Dict[str, Any]:
    """
    Main transcription task.
    
    Args:
        job_id: Job ID
        audio_path: Path to audio file
        params: Processing parameters
    
    Returns:
        Dictionary with job results
    """
    logger.info(f"Starting transcription job {job_id}")
    add_log(job_id, "INFO", f"Starting transcription job")
    
    try:
        # Update job status
        update_job_status(job_id, status="running", progress=5)
        
        # Validate audio file
        logger.info(f"Validating audio file: {audio_path}")
        validate_audio(audio_path, settings.max_duration_sec, settings.max_file_mb)
        add_log(job_id, "INFO", f"Audio validation passed")
        
        # Source separation (optional)
        src_path = audio_path
        if params.get("separation", "none") != "none":
            try:
                logger.info(f"Starting source separation: {params['separation']}")
                sep_dir = os.path.join(settings.storage_dir, f"job_{job_id}", "separation")
                src_path = separate_sources(audio_path, sep_dir, params["separation"])
                add_log(job_id, "INFO", f"Source separation completed: {params['separation']}")
            except Exception as e:
                logger.warning(f"Source separation failed: {e}, using original audio")
                add_log(job_id, "WARNING", f"Source separation failed: {e}")
        
        # Load and preprocess audio
        logger.info("Loading audio")
        y, sr = load_audio_to_mono(src_path, settings.default_sr)
        add_log(job_id, "INFO", f"Audio loaded: {len(y)} samples, {sr} Hz")
        
        # Apply preprocessing
        logger.info("Applying preprocessing")
        y = pp.apply_preprocessing_pipeline(
            y, sr,
            highpass_enabled=params.get("highpass", True),
            normalize_enabled=params.get("normalize", True),
            trim_enabled=params.get("trim", True),
            denoise_enabled=params.get("denoise", True)
        )
        add_log(job_id, "INFO", "Preprocessing completed")
        
        update_job_status(job_id, progress=25)
        
        # F0 estimation
        logger.info("Estimating F0")
        f0_method = params.get("f0_backend", "torchcrepe")
        t, f0_hz, voiced = estimate_f0(y, sr, method=f0_method, smooth=True)
        add_log(job_id, "INFO", f"F0 estimation completed: {len(f0_hz)} frames, {voiced.sum()} voiced")
        
        update_job_status(job_id, progress=45)
        
        # Tempo estimation and rhythm quantization
        logger.info("Estimating tempo and quantizing rhythm")
        qpm = float(params.get("tempo_qpm") or estimate_tempo(y, sr))
        onsets_beats, dur_beats = quantize_rhythm(
            t, qpm, 
            grid=params.get("quantization_grid", 0.25),
            min_note_duration=params.get("min_note_duration", 0.125)
        )
        add_log(job_id, "INFO", f"Rhythm quantization completed: {len(onsets_beats)} notes, {qpm} BPM")
        
        # Key detection
        midi_pitches = f0_to_midi(f0_hz.tolist())
        if params.get("auto_key", True):
            midi_key = detect_key_from_pitches([m for m in midi_pitches if m > 0])
        else:
            midi_key = params.get("key_signature", "C")
        add_log(job_id, "INFO", f"Key detection: {midi_key}")
        
        update_job_status(job_id, progress=65)
        
        # Build score
        logger.info("Building musical score")
        ts = params.get("time_signature", default_time_signature())
        score = build_score(
            midi_pitches, onsets_beats, dur_beats,
            key_signature=midi_key,
            time_signature=ts,
            qpm=qpm,
            title=params.get("title", "Extracted Melody")
        )
        add_log(job_id, "INFO", "Score building completed")
        
        # Create job directory
        job_dir = os.path.join(settings.storage_dir, f"job_{job_id}")
        os.makedirs(job_dir, exist_ok=True)
        
        # Export MusicXML
        logger.info("Exporting MusicXML")
        musicxml_path = os.path.join(job_dir, "score.musicxml")
        export_musicxml(score, musicxml_path)
        add_artifact(job_id, "musicxml", musicxml_path)
        add_log(job_id, "INFO", "MusicXML exported")
        
        update_job_status(job_id, progress=80)
        
        # Generate audio preview
        logger.info("Generating audio preview")
        synth_type = params.get("synthesis_type", "sine")
        y_synth = synth_audio(midi_pitches, onsets_beats, dur_beats, qpm, sr=sr, synth_type=synth_type)
        preview_path = os.path.join(job_dir, "preview.wav")
        sf.write(preview_path, y_synth, sr)
        add_artifact(job_id, "audio_preview", preview_path)
        add_log(job_id, "INFO", f"Audio preview generated: {synth_type}")
        
        # Render PDF/PNG
        logger.info("Rendering PDF/PNG")
        pdf_path = os.path.join(job_dir, "score.pdf")
        png_path = os.path.join(job_dir, "score.png")
        outputs = render_to_pdf_png(musicxml_path, pdf_path, png_path)
        
        for output_path in outputs:
            kind = "pdf" if output_path.endswith(".pdf") else "png"
            add_artifact(job_id, kind, output_path)
        
        add_log(job_id, "INFO", f"Rendering completed: {len(outputs)} files")
        
        # Finalize job
        update_job_status(job_id, status="done", progress=100, finished_at=datetime.utcnow())
        add_log(job_id, "INFO", "Transcription job completed successfully")
        
        logger.info(f"Transcription job {job_id} completed successfully")
        
        return {
            "job_id": job_id,
            "status": "done",
            "artifacts": [musicxml_path, preview_path] + outputs,
            "metadata": {
                "tempo": qpm,
                "key": midi_key,
                "time_signature": ts,
                "notes_count": len(onsets_beats),
                "duration_seconds": len(y) / sr
            }
        }
        
    except Exception as e:
        error_msg = f"Transcription failed: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        update_job_status(job_id, status="failed", error=error_msg)
        add_log(job_id, "ERROR", error_msg)
        raise

@celery_app.task(name="cleanup_old_data")
def cleanup_old_data(days: int = None) -> Dict[str, int]:
    """Clean up old data."""
    from app.db.repository import cleanup_old_data as db_cleanup
    
    days = days or settings.cleanup_ttl_days
    logger.info(f"Starting cleanup of data older than {days} days")
    
    try:
        deleted_counts = db_cleanup(days)
        logger.info(f"Cleanup completed: {deleted_counts}")
        return deleted_counts
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return {"uploads": 0, "jobs": 0, "artifacts": 0, "logs": 0}

@celery_app.task(name="get_job_status")
def get_job_status(job_id: int) -> Dict[str, Any]:
    """Get job status and metadata."""
    try:
        job = get_job(job_id)
        if not job:
            return {"error": "Job not found"}
        
        artifacts = []
        for kind in ["musicxml", "pdf", "png", "audio_preview"]:
            artifact = get_artifact_by_kind(job_id, kind)
            if artifact:
                artifacts.append({"kind": kind, "path": artifact.path})
        
        return {
            "job_id": job_id,
            "status": job.status,
            "progress": job.progress,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
            "error": job.error,
            "artifacts": artifacts
        }
    except Exception as e:
        logger.error(f"Failed to get job status {job_id}: {e}")
        return {"error": str(e)}
