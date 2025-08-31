from __future__ import annotations
import logging
import numpy as np
import librosa
from typing import Tuple, List

logger = logging.getLogger(__name__)

def estimate_tempo(y: np.ndarray, sr: int, 
                  hop_length: int = 512,
                  start_bpm: float = 120.0,
                  std_bpm: float = 1.0) -> float:
    """
    Estimate tempo from audio signal.
    
    Args:
        y: Audio signal
        sr: Sample rate
        hop_length: Hop length for beat tracking
        start_bpm: Starting BPM for tempo estimation
        std_bpm: Standard deviation for tempo estimation
    
    Returns:
        Estimated tempo in BPM
    """
    if len(y) == 0:
        logger.warning("Empty audio signal for tempo estimation")
        return 120.0
    
    logger.debug(f"Estimating tempo: sr={sr}, hop_length={hop_length}")
    
    try:
        tempo, beats = librosa.beat.beat_track(
            y=y, sr=sr, hop_length=hop_length,
            start_bpm=start_bpm
        )
        
        logger.debug(f"Tempo estimation result: {tempo:.1f} BPM, {len(beats)} beats")
        
        # Ensure tempo is a scalar
        if hasattr(tempo, '__len__'):
            tempo = float(tempo[0]) if len(tempo) > 0 else start_bpm
        
        # Validate tempo
        if tempo <= 0 or tempo > 300:
            logger.warning(f"Invalid tempo: {tempo:.1f} BPM, using default")
            tempo = start_bpm
        
        return float(tempo)
        
    except Exception as e:
        logger.error(f"Tempo estimation failed: {e}")
        return 120.0

def times_to_beats(times: np.ndarray, tempo_bpm: float) -> np.ndarray:
    """
    Convert time positions to beat positions.
    
    Args:
        times: Time positions in seconds
        tempo_bpm: Tempo in BPM
    
    Returns:
        Beat positions
    """
    if len(times) == 0:
        return times
    
    if tempo_bpm <= 0:
        logger.warning(f"Invalid tempo: {tempo_bpm} BPM")
        return times
    
    seconds_per_beat = 60.0 / tempo_bpm
    beats = times / seconds_per_beat
    
    logger.debug(f"Converted {len(times)} time positions to beats at {tempo_bpm} BPM")
    return beats

def quantize_beats(beat_positions: np.ndarray, grid: float = 0.25) -> np.ndarray:
    """
    Quantize beat positions to grid.
    
    Args:
        beat_positions: Beat positions
        grid: Grid size in beats (e.g., 0.25 = 16th note)
    
    Returns:
        Quantized beat positions
    """
    if len(beat_positions) == 0:
        return beat_positions
    
    if grid <= 0:
        logger.warning(f"Invalid grid size: {grid}")
        return beat_positions
    
    quantized = np.round(beat_positions / grid) * grid
    
    logger.debug(f"Quantized {len(beat_positions)} beats to grid {grid}")
    return quantized

def collapse_short_notes(onsets: np.ndarray, durations: np.ndarray, 
                        min_duration: float = 0.125) -> Tuple[np.ndarray, np.ndarray]:
    """
    Collapse notes shorter than minimum duration.
    
    Args:
        onsets: Note onset times in beats
        durations: Note durations in beats
        min_duration: Minimum note duration in beats
    
    Returns:
        Tuple of (filtered_onsets, filtered_durations)
    """
    if len(onsets) == 0:
        return onsets, durations
    
    # Filter out notes shorter than minimum duration
    valid_mask = durations >= min_duration
    
    if not np.any(valid_mask):
        logger.warning("No notes meet minimum duration requirement")
        return np.array([]), np.array([])
    
    filtered_onsets = onsets[valid_mask]
    filtered_durations = durations[valid_mask]
    
    logger.debug(f"Collapsed notes: {len(onsets)} -> {len(filtered_onsets)}")
    return filtered_onsets, filtered_durations

def insert_rests(onsets: np.ndarray, durations: np.ndarray, 
                total_duration: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Insert rests to fill gaps between notes.
    
    Args:
        onsets: Note onset times in beats
        durations: Note durations in beats
        total_duration: Total duration in beats
    
    Returns:
        Tuple of (all_onsets, all_durations)
    """
    if len(onsets) == 0:
        return np.array([0.0]), np.array([total_duration])
    
    # Sort by onset time
    sorted_indices = np.argsort(onsets)
    sorted_onsets = onsets[sorted_indices]
    sorted_durations = durations[sorted_indices]
    
    all_onsets = []
    all_durations = []
    
    current_time = 0.0
    
    for onset, duration in zip(sorted_onsets, sorted_durations):
        # Add rest if there's a gap
        if onset > current_time:
            rest_duration = onset - current_time
            all_onsets.append(current_time)
            all_durations.append(rest_duration)
        
        # Add note
        all_onsets.append(onset)
        all_durations.append(duration)
        current_time = onset + duration
    
    # Add final rest if needed
    if current_time < total_duration:
        all_onsets.append(current_time)
        all_durations.append(total_duration - current_time)
    
    logger.debug(f"Inserted rests: {len(onsets)} notes -> {len(all_onsets)} events")
    return np.array(all_onsets), np.array(all_durations)

def quantize_rhythm(times: np.ndarray, tempo_bpm: float, 
                   grid: float = 0.25,
                   min_note_duration: float = 0.125) -> Tuple[np.ndarray, np.ndarray]:
    """
    Complete rhythm quantization pipeline.
    
    Args:
        times: Time positions in seconds
        tempo_bpm: Tempo in BPM
        grid: Grid size in beats
        min_note_duration: Minimum note duration in beats
    
    Returns:
        Tuple of (quantized_onsets, quantized_durations)
    """
    if len(times) == 0:
        return np.array([]), np.array([])
    
    logger.info(f"Starting rhythm quantization: {len(times)} events at {tempo_bpm} BPM")
    
    # Convert times to beats
    beats = times_to_beats(times, tempo_bpm)
    
    # Quantize to grid
    quantized_beats = quantize_beats(beats, grid)
    
    # Calculate durations (assuming equal spacing for now)
    if len(quantized_beats) > 1:
        durations = np.diff(quantized_beats)
        durations = np.append(durations, grid)  # Last note gets default duration
    else:
        durations = np.array([grid])
    
    # Collapse short notes
    onsets, durations = collapse_short_notes(quantized_beats, durations, min_note_duration)
    
    logger.info(f"Rhythm quantization completed: {len(onsets)} notes")
    return onsets, durations
