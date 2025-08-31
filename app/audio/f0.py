from __future__ import annotations
import logging
import numpy as np
import librosa
from typing import Tuple

logger = logging.getLogger(__name__)

try:
    import torchcrepe  # type: ignore
    TORCHCREPE_AVAILABLE = True
except ImportError:
    logger.warning("torchcrepe not available, falling back to pYIN")
    TORCHCREPE_AVAILABLE = False

def estimate_f0_pyin(y: np.ndarray, sr: int, 
                    frame_length: int = 2048, 
                    hop_length: int = 160,
                    fmin: float = None,
                    fmax: float = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Estimate F0 using pYIN algorithm.
    
    Args:
        y: Audio signal
        sr: Sample rate
        frame_length: Frame length for STFT
        hop_length: Hop length for STFT
        fmin: Minimum frequency (Hz)
        fmax: Maximum frequency (Hz)
    
    Returns:
        Tuple of (times, f0_hz, voiced_flag)
    """
    if len(y) == 0:
        return np.array([]), np.array([]), np.array([])
    
    if fmin is None:
        fmin = librosa.note_to_hz("C2")  # ~65 Hz
    if fmax is None:
        fmax = librosa.note_to_hz("C7")  # ~2093 Hz
    
    logger.debug(f"pYIN F0 estimation: sr={sr}, frame_length={frame_length}, hop_length={hop_length}")
    
    try:
        f0, voiced_flag, _ = librosa.pyin(
            y,
            fmin=fmin,
            fmax=fmax,
            frame_length=frame_length,
            hop_length=hop_length,
            sr=sr,
            fill_na=0.0
        )
        
        t = librosa.frames_to_time(np.arange(len(f0)), sr=sr, hop_length=hop_length)
        f0_hz = np.where(np.isnan(f0), 0.0, f0)
        
        logger.debug(f"pYIN completed: frames={len(f0)}, voiced_frames={voiced_flag.sum()}")
        return t.astype(np.float32), f0_hz.astype(np.float32), voiced_flag.astype(bool)
        
    except Exception as e:
        logger.error(f"pYIN F0 estimation failed: {e}")
        raise

def estimate_f0_torchcrepe(y: np.ndarray, sr: int, 
                         hop_seconds: float = 0.01,
                         fmin: float = 50.0,
                         fmax: float = 1100.0,
                         model: str = "full") -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Estimate F0 using torchcrepe.
    
    Args:
        y: Audio signal
        sr: Sample rate
        hop_seconds: Hop size in seconds
        fmin: Minimum frequency (Hz)
        fmax: Maximum frequency (Hz)
        model: Model type (full, tiny)
    
    Returns:
        Tuple of (times, f0_hz, voiced_flag)
    """
    if not TORCHCREPE_AVAILABLE:
        raise RuntimeError("torchcrepe не установлен")
    
    if len(y) == 0:
        return np.array([]), np.array([]), np.array([])
    
    logger.debug(f"torchcrepe F0 estimation: sr={sr}, hop_seconds={hop_seconds}, model={model}")
    
    try:
        import torch
        
        device = "cpu"
        hop_length = int(sr * hop_seconds)
        
        # Prepare input tensor
        x = torch.tensor(y, dtype=torch.float32)[None, None, :]
        
        # Predict F0
        f0 = torchcrepe.predict(
            x, sr, hop_length,
            fmin=fmin, fmax=fmax,
            model=model, 
            batch_size=1024, 
            device=device, 
            return_periodicity=False,
        )[0]
        
        f0 = f0.numpy()
        t = np.arange(len(f0)) * hop_seconds
        voiced = f0 > 0
        
        logger.debug(f"torchcrepe completed: frames={len(f0)}, voiced_frames={voiced.sum()}")
        return t.astype(np.float32), f0.astype(np.float32), voiced.astype(bool)
        
    except Exception as e:
        logger.error(f"torchcrepe F0 estimation failed: {e}")
        raise

def smooth_f0(f0: np.ndarray, voiced: np.ndarray, 
             median_window: int = 5,
             viterbi: bool = True) -> np.ndarray:
    """
    Smooth F0 contour using median filtering and Viterbi smoothing.
    
    Args:
        f0: F0 values
        voiced: Voiced flags
        median_window: Median filter window size
        viterbi: Whether to apply Viterbi smoothing
    
    Returns:
        Smoothed F0 values
    """
    if len(f0) == 0:
        return f0
    
    smoothed = f0.copy()
    
    # Apply median smoothing to voiced regions
    if median_window > 1:
        from scipy.ndimage import median_filter
        smoothed = median_filter(smoothed, size=median_window)
    
    # Apply Viterbi smoothing if requested
    if viterbi and len(smoothed) > 1:
        try:
            # Simple Viterbi-like smoothing
            for i in range(1, len(smoothed)):
                if voiced[i] and voiced[i-1]:
                    # Smooth transition between voiced frames
                    diff = abs(smoothed[i] - smoothed[i-1])
                    if diff > smoothed[i-1] * 0.1:  # More than 10% change
                        smoothed[i] = smoothed[i-1] * 0.9 + smoothed[i] * 0.1
        except Exception as e:
            logger.warning(f"Viterbi smoothing failed: {e}")
    
    return smoothed

def estimate_f0(y: np.ndarray, sr: int, 
               method: str = "torchcrepe",
               smooth: bool = True) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Estimate F0 using specified method with optional smoothing.
    
    Args:
        y: Audio signal
        sr: Sample rate
        method: F0 estimation method (torchcrepe, pyin)
        smooth: Whether to apply smoothing
    
    Returns:
        Tuple of (times, f0_hz, voiced_flag)
    """
    if method == "torchcrepe":
        if TORCHCREPE_AVAILABLE:
            t, f0, voiced = estimate_f0_torchcrepe(y, sr)
        else:
            logger.warning("torchcrepe not available, falling back to pYIN")
            t, f0, voiced = estimate_f0_pyin(y, sr)
    elif method == "pyin":
        t, f0, voiced = estimate_f0_pyin(y, sr)
    else:
        raise ValueError(f"Unknown F0 method: {method}. Supported: torchcrepe, pyin")
    
    if smooth and len(f0) > 0:
        f0 = smooth_f0(f0, voiced)
    
    return t, f0, voiced
