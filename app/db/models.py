from __future__ import annotations
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import String, Integer, JSON, ForeignKey, DateTime, Column

Base = declarative_base()

class Upload(Base):
    __tablename__ = "uploads"
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(512))
    ext = Column(String(16))
    sr = Column(Integer)
    duration_sec = Column(Integer)
    size_bytes = Column(Integer)
    path = Column(String(1024))
    created_at = Column(DateTime, default=datetime.utcnow)
    jobs = relationship("Job", back_populates="upload")

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    upload_id = Column(Integer, ForeignKey("uploads.id"))
    params_json = Column(JSON)
    status = Column(String(16), default="queued")
    progress = Column(Integer, default=0)
    error = Column(String(2048), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    upload = relationship("Upload", back_populates="jobs")
    artifacts = relationship("Artifact", back_populates="job")

class Artifact(Base):
    __tablename__ = "artifacts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    kind = Column(String(32))  # musicxml|pdf|png|audio_preview
    path = Column(String(1024))
    created_at = Column(DateTime, default=datetime.utcnow)
    job = relationship("Job", back_populates="artifacts")
