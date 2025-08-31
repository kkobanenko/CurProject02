from __future__ import annotations
import logging
from sqlalchemy import text
from app.db.repository import engine

logger = logging.getLogger(__name__)

def run_migrations():
    """Run database migrations."""
    try:
        with engine.connect() as conn:
            # Create indexes if they don't exist
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_uploads_created_at ON uploads(created_at);
                CREATE INDEX IF NOT EXISTS idx_jobs_status_created ON jobs(status, created_at);
                CREATE INDEX IF NOT EXISTS idx_jobs_upload_id ON jobs(upload_id);
                CREATE INDEX IF NOT EXISTS idx_artifacts_job_kind ON artifacts(job_id, kind);
            """))
            
            # Add foreign key constraints if they don't exist
            conn.execute(text("""
                ALTER TABLE jobs ADD CONSTRAINT IF NOT EXISTS fk_jobs_upload_id 
                FOREIGN KEY (upload_id) REFERENCES uploads(id) ON DELETE CASCADE;
                
                ALTER TABLE artifacts ADD CONSTRAINT IF NOT EXISTS fk_artifacts_job_id 
                FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE;
            """))
            
            conn.commit()
            logger.info("Database migrations completed successfully")
            
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        raise

def create_logs_table():
    """Create logs table if it doesn't exist."""
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS logs (
                    id SERIAL PRIMARY KEY,
                    job_id INTEGER NOT NULL,
                    level VARCHAR(16) NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_logs_job_id ON logs(job_id);
                CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level);
                CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at);
                
                ALTER TABLE logs ADD CONSTRAINT IF NOT EXISTS fk_logs_job_id 
                FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE;
            """))
            
            conn.commit()
            logger.info("Logs table created successfully")
            
    except Exception as e:
        logger.error(f"Failed to create logs table: {e}")
        raise
