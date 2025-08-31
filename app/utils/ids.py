"""
ID generation utilities for the application.
"""
from __future__ import annotations
import uuid
import hashlib
from datetime import datetime
from typing import Optional

def generate_job_id() -> str:
    """Generate a unique job ID."""
    return f"job_{uuid.uuid4().hex[:8]}"

def generate_upload_id() -> str:
    """Generate a unique upload ID."""
    return f"upload_{uuid.uuid4().hex[:8]}"

def generate_correlation_id() -> str:
    """Generate a correlation ID for logging."""
    return f"corr_{uuid.uuid4().hex[:8]}"

def generate_file_id(filename: str, timestamp: Optional[datetime] = None) -> str:
    """Generate a file ID based on filename and timestamp."""
    if timestamp is None:
        timestamp = datetime.utcnow()
    
    # Create a hash of filename and timestamp
    content = f"{filename}_{timestamp.isoformat()}"
    file_hash = hashlib.md5(content.encode()).hexdigest()[:8]
    
    return f"file_{file_hash}"

def generate_session_id() -> str:
    """Generate a session ID for user sessions."""
    return f"session_{uuid.uuid4().hex[:12]}"
