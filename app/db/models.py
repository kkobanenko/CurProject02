from __future__ import annotations
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import String, Integer, JSON, ForeignKey, DateTime, Column, Index, Text, Boolean

Base = declarative_base()

class Upload(Base):
    """Uploaded audio file information."""
    __tablename__ = "uploads"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(512), nullable=False, index=True)
    ext = Column(String(16), nullable=False)
    sr = Column(Integer, nullable=False)  # Sample rate
    duration_sec = Column(Integer, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    path = Column(String(1024), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    jobs = relationship("Job", back_populates="upload", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Upload(id={self.id}, filename='{self.filename}', size={self.size_bytes})>"

class Job(Base):
    """Processing job information."""
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    upload_id = Column(Integer, ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False, index=True)
    params_json = Column(JSON, nullable=False)  # Processing parameters
    status = Column(String(16), default="queued", nullable=False, index=True)  # queued, running, done, failed
    progress = Column(Integer, default=0, nullable=False)  # 0-100
    error = Column(Text, nullable=True)  # Error message if failed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    finished_at = Column(DateTime, nullable=True)
    
    # Relationships
    upload = relationship("Upload", back_populates="jobs")
    artifacts = relationship("Artifact", back_populates="job", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Job(id={self.id}, status='{self.status}', progress={self.progress})>"

class Artifact(Base):
    """Generated artifacts (files)."""
    __tablename__ = "artifacts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    kind = Column(String(32), nullable=False, index=True)  # musicxml, pdf, png, audio_preview, midi
    path = Column(String(1024), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    job = relationship("Job", back_populates="artifacts")
    
    def __repr__(self):
        return f"<Artifact(id={self.id}, kind='{self.kind}', path='{self.path}')>"

class Log(Base):
    """Job processing logs."""
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    level = Column(String(16), nullable=False, index=True)  # DEBUG, INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<Log(id={self.id}, level='{self.level}', job_id={self.job_id})>"

# Indexes for better query performance
Index('idx_uploads_created_at', Upload.created_at)
Index('idx_jobs_status_created', Job.status, Job.created_at)
Index('idx_jobs_upload_id', Job.upload_id)
Index('idx_artifacts_job_kind', Artifact.job_id, Artifact.kind)
Index('idx_logs_job_level', Log.job_id, Log.level)
