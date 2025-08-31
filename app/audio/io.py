from __future__ import annotations
import os
from typing import Tuple
import librosa
import numpy as np
from app.settings import settings

ALLOWED_EXT = {"mp3", "wav", "flac", "m4a", "ogg"}

def load_audio_to_mono(path: str, target_sr: int | None = None) -> Tuple[np.ndarray, int]:
    y, sr = librosa.load(path, sr=target_sr or settings.default_sr, mono=True)
    return y.astype(np.float32), sr

def validate_audio(path: str, max_seconds: int, max_mb: int) -> None:
    ext = os.path.splitext(path)[1].lstrip(".").lower()
    if ext not in ALLOWED_EXT:
        raise ValueError(f"Недопустимый формат: .{ext}")
    size_mb = os.path.getsize(path) / (1024 * 1024)
    if size_mb > max_mb:
        raise ValueError(f"Файл слишком большой: {size_mb:.1f} МБ > {max_mb} МБ")
    duration = librosa.get_duration(path=path)
    if duration > max_seconds:
        raise ValueError(f"Длительность {duration:.1f}s > {max_seconds}s")
