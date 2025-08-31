-- Database schema for Melody2Score application

-- Uploads table
CREATE TABLE IF NOT EXISTS uploads (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(512) NOT NULL,
    ext VARCHAR(16) NOT NULL,
    sr INTEGER NOT NULL,
    duration_sec INTEGER NOT NULL,
    size_bytes INTEGER NOT NULL,
    path VARCHAR(1024) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    upload_id INTEGER NOT NULL REFERENCES uploads(id) ON DELETE CASCADE,
    params_json JSONB NOT NULL,
    status VARCHAR(16) DEFAULT 'queued' NOT NULL,
    progress INTEGER DEFAULT 0 NOT NULL,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    finished_at TIMESTAMP
);

-- Artifacts table
CREATE TABLE IF NOT EXISTS artifacts (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    kind VARCHAR(32) NOT NULL,
    path VARCHAR(1024) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Logs table
CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    level VARCHAR(16) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_uploads_created_at ON uploads(created_at);
CREATE INDEX IF NOT EXISTS idx_uploads_filename ON uploads(filename);
CREATE INDEX IF NOT EXISTS idx_jobs_status_created ON jobs(status, created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_upload_id ON jobs(upload_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_job_kind ON artifacts(job_id, kind);
CREATE INDEX IF NOT EXISTS idx_logs_job_level ON logs(job_id, level);
CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at);
