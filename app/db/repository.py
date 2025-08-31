from __future__ import annotations
from contextlib import contextmanager
from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker
from .models import Base, Upload, Job, Artifact
from app.settings import settings

engine = create_engine(settings.postgres_dsn, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)

def init_db() -> None:
    Base.metadata.create_all(engine)

@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def create_upload(**kwargs) -> Upload:
    with session_scope() as s:
        up = Upload(**kwargs)
        s.add(up)
        s.flush()
        return up

def create_job(upload_id: int, params_json: dict) -> Job:
    with session_scope() as s:
        job = Job(upload_id=upload_id, params_json=params_json)
        s.add(job)
        s.flush()
        return job

def update_job_status(job_id: int, **fields) -> None:
    with session_scope() as s:
        s.execute(update(Job).where(Job.id == job_id).values(**fields))

def add_artifact(job_id: int, kind: str, path: str) -> Artifact:
    with session_scope() as s:
        art = Artifact(job_id=job_id, kind=kind, path=path)
        s.add(art)
        s.flush()
        return art

def get_job(job_id: int) -> Job | None:
    with session_scope() as s:
        return s.get(Job, job_id)
