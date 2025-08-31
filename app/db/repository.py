from __future__ import annotations
import logging
from contextlib import contextmanager
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import create_engine, update, select, delete, desc, asc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from .models import Base, Upload, Job, Artifact, Log
from app.settings import settings

logger = logging.getLogger(__name__)

# Database engine and session
engine = create_engine(
    settings.postgres_dsn, 
    echo=False, 
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)

def init_db() -> None:
    """Initialize database tables."""
    try:
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

def check_db_connection() -> bool:
    """Check database connection."""
    try:
        with engine.connect() as conn:
            conn.execute(select(1))
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {e}")
        return False

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()

# Upload operations
def create_upload(**kwargs) -> Upload:
    """Create a new upload record."""
    try:
        with session_scope() as s:
            up = Upload(**kwargs)
            s.add(up)
            s.flush()
            logger.info(f"Created upload: {up.id}")
            return up
    except SQLAlchemyError as e:
        logger.error(f"Failed to create upload: {e}")
        raise

def get_upload(upload_id: int) -> Optional[Upload]:
    """Get upload by ID."""
    try:
        with session_scope() as s:
            return s.get(Upload, upload_id)
    except SQLAlchemyError as e:
        logger.error(f"Failed to get upload {upload_id}: {e}")
        return None

def get_uploads(limit: int = 100, offset: int = 0) -> List[Upload]:
    """Get recent uploads."""
    try:
        with session_scope() as s:
            return s.query(Upload).order_by(desc(Upload.created_at)).limit(limit).offset(offset).all()
    except SQLAlchemyError as e:
        logger.error(f"Failed to get uploads: {e}")
        return []

def delete_upload(upload_id: int) -> bool:
    """Delete upload and all related data."""
    try:
        with session_scope() as s:
            upload = s.get(Upload, upload_id)
            if upload:
                s.delete(upload)
                logger.info(f"Deleted upload: {upload_id}")
                return True
            return False
    except SQLAlchemyError as e:
        logger.error(f"Failed to delete upload {upload_id}: {e}")
        return False

# Job operations
def create_job(upload_id: int, params_json: dict) -> Job:
    """Create a new job record."""
    try:
        with session_scope() as s:
            job = Job(upload_id=upload_id, params_json=params_json)
            s.add(job)
            s.flush()
            logger.info(f"Created job: {job.id} for upload: {upload_id}")
            return job
    except SQLAlchemyError as e:
        logger.error(f"Failed to create job: {e}")
        raise

def get_job(job_id: int) -> Optional[Job]:
    """Get job by ID."""
    try:
        with session_scope() as s:
            return s.get(Job, job_id)
    except SQLAlchemyError as e:
        logger.error(f"Failed to get job {job_id}: {e}")
        return None

def get_jobs_by_upload(upload_id: int) -> List[Job]:
    """Get all jobs for an upload."""
    try:
        with session_scope() as s:
            return s.query(Job).filter(Job.upload_id == upload_id).order_by(desc(Job.created_at)).all()
    except SQLAlchemyError as e:
        logger.error(f"Failed to get jobs for upload {upload_id}: {e}")
        return []

def get_jobs_by_status(status: str, limit: int = 100) -> List[Job]:
    """Get jobs by status."""
    try:
        with session_scope() as s:
            return s.query(Job).filter(Job.status == status).order_by(desc(Job.created_at)).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Failed to get jobs with status {status}: {e}")
        return []

def update_job_status(job_id: int, **fields) -> bool:
    """Update job status and other fields."""
    try:
        with session_scope() as s:
            result = s.execute(update(Job).where(Job.id == job_id).values(**fields))
            if result.rowcount > 0:
                logger.info(f"Updated job {job_id}: {fields}")
                return True
            return False
    except SQLAlchemyError as e:
        logger.error(f"Failed to update job {job_id}: {e}")
        return False

def delete_job(job_id: int) -> bool:
    """Delete job and all related artifacts."""
    try:
        with session_scope() as s:
            job = s.get(Job, job_id)
            if job:
                s.delete(job)
                logger.info(f"Deleted job: {job_id}")
                return True
            return False
    except SQLAlchemyError as e:
        logger.error(f"Failed to delete job {job_id}: {e}")
        return False

# Artifact operations
def add_artifact(job_id: int, kind: str, path: str) -> Artifact:
    """Add an artifact record."""
    try:
        with session_scope() as s:
            art = Artifact(job_id=job_id, kind=kind, path=path)
            s.add(art)
            s.flush()
            logger.info(f"Added artifact: {kind} for job: {job_id}")
            return art
    except SQLAlchemyError as e:
        logger.error(f"Failed to add artifact: {e}")
        raise

def get_artifacts_by_job(job_id: int) -> List[Artifact]:
    """Get all artifacts for a job."""
    try:
        with session_scope() as s:
            return s.query(Artifact).filter(Artifact.job_id == job_id).order_by(Artifact.created_at).all()
    except SQLAlchemyError as e:
        logger.error(f"Failed to get artifacts for job {job_id}: {e}")
        return []

def get_artifact_by_kind(job_id: int, kind: str) -> Optional[Artifact]:
    """Get specific artifact by kind."""
    try:
        with session_scope() as s:
            return s.query(Artifact).filter(Artifact.job_id == job_id, Artifact.kind == kind).first()
    except SQLAlchemyError as e:
        logger.error(f"Failed to get artifact {kind} for job {job_id}: {e}")
        return None

def delete_artifact(artifact_id: int) -> bool:
    """Delete artifact record."""
    try:
        with session_scope() as s:
            artifact = s.get(Artifact, artifact_id)
            if artifact:
                s.delete(artifact)
                logger.info(f"Deleted artifact: {artifact_id}")
                return True
            return False
    except SQLAlchemyError as e:
        logger.error(f"Failed to delete artifact {artifact_id}: {e}")
        return False

# Log operations
def add_log(job_id: int, level: str, message: str) -> Log:
    """Add a log entry."""
    try:
        with session_scope() as s:
            log = Log(job_id=job_id, level=level, message=message)
            s.add(log)
            s.flush()
            return log
    except SQLAlchemyError as e:
        logger.error(f"Failed to add log: {e}")
        raise

def get_logs_by_job(job_id: int, limit: int = 100) -> List[Log]:
    """Get logs for a job."""
    try:
        with session_scope() as s:
            return s.query(Log).filter(Log.job_id == job_id).order_by(desc(Log.created_at)).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Failed to get logs for job {job_id}: {e}")
        return []

# Cleanup operations
def cleanup_old_data(days: int = 7) -> Dict[str, int]:
    """Clean up old data."""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    deleted_counts = {"uploads": 0, "jobs": 0, "artifacts": 0, "logs": 0}
    
    try:
        with session_scope() as s:
            # Delete old uploads (cascades to jobs, artifacts, logs)
            result = s.execute(delete(Upload).where(Upload.created_at < cutoff_date))
            deleted_counts["uploads"] = result.rowcount
            
            logger.info(f"Cleanup completed: {deleted_counts}")
            return deleted_counts
    except SQLAlchemyError as e:
        logger.error(f"Cleanup failed: {e}")
        return deleted_counts

def get_database_stats() -> Dict[str, Any]:
    """Get database statistics."""
    try:
        with session_scope() as s:
            stats = {
                "uploads": s.query(Upload).count(),
                "jobs": s.query(Job).count(),
                "artifacts": s.query(Artifact).count(),
                "logs": s.query(Log).count(),
                "jobs_by_status": {}
            }
            
            # Count jobs by status
            for status in ["queued", "running", "done", "failed"]:
                stats["jobs_by_status"][status] = s.query(Job).filter(Job.status == status).count()
            
            return stats
    except SQLAlchemyError as e:
        logger.error(f"Failed to get database stats: {e}")
        return {}
