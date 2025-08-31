from __future__ import annotations
import os
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Storage
    storage_dir: str = Field(default="/data", description="Directory for file storage")
    max_file_mb: int = Field(default=100, description="Maximum file size in MB")
    max_duration_sec: int = Field(default=300, description="Maximum audio duration in seconds")
    default_sr: int = Field(default=22050, description="Default sample rate")
    
    # Rendering
    renderer: str = Field(default="mscore", description="Renderer: mscore|verovio|none")
    musescore_path: str = Field(default="/snap/bin/musescore.mscore", description="Path to MuseScore executable")
    verovio_path: str = Field(default="verovio", description="Path to Verovio executable")
    render_timeout_sec: int = Field(default=60, description="Render timeout in seconds")
    
    # Infrastructure
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    postgres_dsn: str = Field(
        default="postgresql+psycopg2://app:app@localhost:5432/m2s",
        description="PostgreSQL connection string"
    )
    cleanup_ttl_days: int = Field(default=7, description="Cleanup TTL in days")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
