from __future__ import annotations
import numpy as np
import librosa

def estimate_tempo(y: np.ndarray, sr: int) -> float:
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    return float(tempo)

def times_to_beats(times: np.ndarray, tempo_bpm: float) -> np.ndarray:
    seconds_per_beat = 60.0 / tempo_bpm
    return times / seconds_per_beat

def quantize_beats(beat_positions: np.ndarray, grid: float = 0.25) -> np.ndarray:
    return np.round(beat_positions / grid) * grid
