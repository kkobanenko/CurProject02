from __future__ import annotations
import logging
from typing import Dict, Any, Optional
from app.tasks.celery_tasks import celery_app, transcribe_job, get_job_status
from app.db.repository import create_job, get_job, get_artifacts_by_job

logger = logging.getLogger(__name__)

def submit_transcription_job(upload_id: int, audio_path: str, params: dict) -> Dict[str, Any]:
    """
    Submit a transcription job.
    
    Args:
        upload_id: Upload ID
        audio_path: Path to audio file
        params: Processing parameters
    
    Returns:
        Dictionary with job information
    """
    try:
        # Create job record
        job = create_job(upload_id, params)
        logger.info(f"Created job {job.id} for upload {upload_id}")
        
        # Submit task
        task_result = transcribe_job.apply_async(
            args=[job.id, audio_path, params],
            queue='default',
            retry=True,
            retry_policy={
                'max_retries': 3,
                'interval_start': 0,
                'interval_step': 0.2,
                'interval_max': 0.2,
            }
        )
        
        logger.info(f"Submitted transcription task {task_result.id} for job {job.id}")
        
        return {
            "job_id": job.id,
            "task_id": task_result.id,
            "status": "queued",
            "upload_id": upload_id
        }
        
    except Exception as e:
        logger.error(f"Failed to submit transcription job: {e}")
        raise

def get_job_progress(job_id: int) -> Dict[str, Any]:
    """
    Get job progress and status.
    
    Args:
        job_id: Job ID
    
    Returns:
        Dictionary with job progress information
    """
    try:
        job = get_job(job_id)
        if not job:
            return {"error": "Job not found"}
        
        # Get artifacts
        artifacts = get_artifacts_by_job(job_id)
        artifact_info = [{"kind": a.kind, "path": a.path} for a in artifacts]
        
        return {
            "job_id": job_id,
            "status": job.status,
            "progress": job.progress,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
            "error": job.error,
            "artifacts": artifact_info
        }
        
    except Exception as e:
        logger.error(f"Failed to get job progress {job_id}: {e}")
        return {"error": str(e)}

def cancel_job(job_id: int) -> bool:
    """
    Cancel a running job.
    
    Args:
        job_id: Job ID
    
    Returns:
        True if cancelled successfully
    """
    try:
        job = get_job(job_id)
        if not job:
            logger.warning(f"Job {job_id} not found")
            return False
        
        if job.status not in ["queued", "running"]:
            logger.warning(f"Job {job_id} cannot be cancelled (status: {job.status})")
            return False
        
        # Revoke task if it's running
        celery_app.control.revoke(job_id, terminate=True)
        
        # Update job status
        from app.db.repository import update_job_status
        update_job_status(job_id, status="cancelled", error="Job cancelled by user")
        
        logger.info(f"Job {job_id} cancelled successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {e}")
        return False

def get_queue_status() -> Dict[str, Any]:
    """
    Get Celery queue status.
    
    Returns:
        Dictionary with queue information
    """
    try:
        inspect = celery_app.control.inspect()
        
        active = inspect.active()
        reserved = inspect.reserved()
        registered = inspect.registered()
        
        return {
            "active_tasks": len(active.get('default', [])) if active else 0,
            "reserved_tasks": len(reserved.get('default', [])) if reserved else 0,
            "registered_tasks": len(registered.get('default', [])) if registered else 0,
            "workers": list(active.keys()) if active else []
        }
        
    except Exception as e:
        logger.error(f"Failed to get queue status: {e}")
        return {
            "active_tasks": 0,
            "reserved_tasks": 0,
            "registered_tasks": 0,
            "workers": [],
            "error": str(e)
        }

def retry_failed_job(job_id: int) -> bool:
    """
    Retry a failed job.
    
    Args:
        job_id: Job ID
    
    Returns:
        True if retry initiated successfully
    """
    try:
        job = get_job(job_id)
        if not job:
            logger.warning(f"Job {job_id} not found")
            return False
        
        if job.status != "failed":
            logger.warning(f"Job {job_id} is not failed (status: {job.status})")
            return False
        
        # Get original parameters
        params = job.params_json
        
        # Get upload path
        upload = job.upload
        if not upload:
            logger.error(f"Upload not found for job {job_id}")
            return False
        
        audio_path = upload.path
        
        # Reset job status
        from app.db.repository import update_job_status
        update_job_status(job_id, status="queued", progress=0, error=None)
        
        # Submit new task
        task_result = transcribe_job.apply_async(
            args=[job_id, audio_path, params],
            queue='default',
            retry=True,
            retry_policy={
                'max_retries': 3,
                'interval_start': 0,
                'interval_step': 0.2,
                'interval_max': 0.2,
            }
        )
        
        logger.info(f"Retried job {job_id} with task {task_result.id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to retry job {job_id}: {e}")
        return False
