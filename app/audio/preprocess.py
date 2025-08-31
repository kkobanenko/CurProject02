from __future__ import annotations
import numpy as np
import librosa

def highpass(y: np.ndarray, sr: int, cutoff_hz: float = 50.0) -> np.ndarray:
    sos = librosa.iirfilter(2, cutoff_hz, btype="highpass", fs=sr, output="sos")
    return librosa.sosfilt(sos, y)

def normalize(y: np.ndarray, target_rms: float = 0.1) -> np.ndarray:
    rms = np.sqrt(np.mean(y**2) + 1e-12)
    if rms == 0:
        return y
    return y * (target_rms / rms)

def trim_silence(y: np.ndarray, top_db: float = 30.0) -> np.ndarray:
    yt, _ = librosa.effects.trim(y, top_db=top_db)
    return yt

def spectral_denoise(y: np.ndarray, sr: int) -> np.ndarray:
    S = librosa.stft(y, n_fft=1024, hop_length=256)
    mag, phase = librosa.magphase(S)
    noise = np.median(mag, axis=1, keepdims=True)
    mask = mag > noise
    S_f = mask * S
    y_out = librosa.istft(S_f, hop_length=256)
    return y_out.astype(y.dtype)
