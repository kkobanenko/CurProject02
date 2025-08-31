from __future__ import annotations
import os
import logging
from typing import Tuple
import librosa
import numpy as np
from app.settings import settings

logger = logging.getLogger(__name__)

ALLOWED_EXT = {"mp3", "wav", "flac", "m4a", "ogg"}

def load_audio_to_mono(path: str, target_sr: int | None = None) -> Tuple[np.ndarray, int]:
    """Load audio file and convert to mono with target sample rate."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Audio file not found: {path}")
    
    target_sr = target_sr or settings.default_sr
    logger.info(f"Loading audio: {path}, target_sr={target_sr}")
    
    try:
        y, sr = librosa.load(path, sr=target_sr, mono=True)
        logger.info(f"Loaded audio: shape={y.shape}, sr={sr}, duration={len(y)/sr:.2f}s")
        return y.astype(np.float32), sr
    except Exception as e:
        logger.error(f"Failed to load audio {path}: {e}")
        raise

def validate_audio(path: str, max_seconds: int, max_mb: int) -> None:
    """Validate audio file format, size and duration."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Audio file not found: {path}")
    
    # Check file extension
    ext = os.path.splitext(path)[1].lstrip(".").lower()
    if ext not in ALLOWED_EXT:
        raise ValueError(f"Недопустимый формат: .{ext}. Поддерживаемые: {', '.join(ALLOWED_EXT)}")
    
    # Check file size
    size_mb = os.path.getsize(path) / (1024 * 1024)
    if size_mb > max_mb:
        raise ValueError(f"Файл слишком большой: {size_mb:.1f} МБ > {max_mb} МБ")
    
    # Check duration
    try:
        duration = librosa.get_duration(path=path)
        if duration > max_seconds:
            raise ValueError(f"Длительность {duration:.1f}s > {max_seconds}s")
        logger.info(f"Audio validation passed: {path}, size={size_mb:.1f}MB, duration={duration:.1f}s")
    except Exception as e:
        logger.error(f"Failed to get duration for {path}: {e}")
        raise ValueError(f"Не удалось определить длительность файла: {e}")

def get_audio_info(path: str) -> dict:
    """Get audio file information."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Audio file not found: {path}")
    
    ext = os.path.splitext(path)[1].lstrip(".").lower()
    size_mb = os.path.getsize(path) / (1024 * 1024)
    
    try:
        duration = librosa.get_duration(path=path)
        y, sr = librosa.load(path, sr=None, mono=True)
        return {
            "filename": os.path.basename(path),
            "extension": ext,
            "size_mb": size_mb,
            "duration_sec": duration,
            "sample_rate": sr,
            "channels": 1 if len(y.shape) == 1 else y.shape[1]
        }
    except Exception as e:
        logger.error(f"Failed to get audio info for {path}: {e}")
        raise
