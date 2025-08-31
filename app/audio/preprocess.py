from __future__ import annotations
import logging
import numpy as np
import librosa

logger = logging.getLogger(__name__)

def highpass(y: np.ndarray, sr: int, cutoff_hz: float = 50.0) -> np.ndarray:
    """Apply high-pass filter to remove low frequency noise."""
    if len(y) == 0:
        return y
    
    logger.debug(f"Applying high-pass filter: cutoff={cutoff_hz}Hz, sr={sr}")
    sos = librosa.iirfilter(2, cutoff_hz, btype="highpass", fs=sr, output="sos")
    filtered = librosa.sosfilt(sos, y)
    logger.debug(f"High-pass filter applied: input_shape={y.shape}, output_shape={filtered.shape}")
    return filtered

def normalize(y: np.ndarray, target_rms: float = 0.1) -> np.ndarray:
    """Normalize audio to target RMS level."""
    if len(y) == 0:
        return y
    
    rms = np.sqrt(np.mean(y**2) + 1e-12)
    if rms == 0:
        logger.warning("Audio is silent, skipping normalization")
        return y
    
    gain = target_rms / rms
    normalized = y * gain
    logger.debug(f"Normalized audio: rms_before={rms:.4f}, rms_after={np.sqrt(np.mean(normalized**2)):.4f}")
    return normalized

def trim_silence(y: np.ndarray, top_db: float = 30.0) -> np.ndarray:
    """Trim silence from beginning and end of audio."""
    if len(y) == 0:
        return y
    
    logger.debug(f"Trimming silence: top_db={top_db}")
    original_length = len(y)
    trimmed, _ = librosa.effects.trim(y, top_db=top_db)
    logger.debug(f"Silence trimmed: {original_length} -> {len(trimmed)} samples")
    return trimmed

def spectral_denoise(y: np.ndarray, sr: int, n_fft: int = 1024, hop_length: int = 256) -> np.ndarray:
    """Apply spectral gating denoising."""
    if len(y) == 0:
        return y
    
    logger.debug(f"Applying spectral denoising: n_fft={n_fft}, hop_length={hop_length}")
    
    # STFT
    S = librosa.stft(y, n_fft=n_fft, hop_length=hop_length)
    mag, phase = librosa.magphase(S)
    
    # Estimate noise from median of magnitude spectrum
    noise = np.median(mag, axis=1, keepdims=True)
    
    # Create binary mask
    mask = mag > noise
    
    # Apply mask
    S_filtered = mask * S
    
    # ISTFT
    y_denoised = librosa.istft(S_filtered, hop_length=hop_length)
    
    # Ensure output has same length as input
    if len(y_denoised) > len(y):
        y_denoised = y_denoised[:len(y)]
    elif len(y_denoised) < len(y):
        y_denoised = np.pad(y_denoised, (0, len(y) - len(y_denoised)), mode='constant')
    
    logger.debug(f"Spectral denoising applied: input_shape={y.shape}, output_shape={y_denoised.shape}")
    return y_denoised.astype(y.dtype)

def apply_preprocessing_pipeline(y: np.ndarray, sr: int, 
                               highpass_enabled: bool = True,
                               normalize_enabled: bool = True,
                               trim_enabled: bool = True,
                               denoise_enabled: bool = True) -> np.ndarray:
    """Apply complete preprocessing pipeline."""
    if len(y) == 0:
        return y
    
    logger.info(f"Starting preprocessing pipeline: shape={y.shape}, sr={sr}")
    processed = y.copy()
    
    if highpass_enabled:
        processed = highpass(processed, sr)
    
    if denoise_enabled:
        processed = spectral_denoise(processed, sr)
    
    if normalize_enabled:
        processed = normalize(processed)
    
    if trim_enabled:
        processed = trim_silence(processed)
    
    logger.info(f"Preprocessing completed: input_shape={y.shape}, output_shape={processed.shape}")
    return processed
