from __future__ import annotations
import logging
import numpy as np
from typing import List, Optional

logger = logging.getLogger(__name__)

def synth_sine(midi_pitches: List[int], 
               onset_beats: List[float], 
               dur_beats: List[float], 
               qpm: float, 
               sr: int = 22050,
               amplitude: float = 0.2,
               fade_samples: int = 100) -> np.ndarray:
    """
    Synthesize audio from MIDI data using sine waves.
    
    Args:
        midi_pitches: List of MIDI pitch numbers
        onset_beats: List of onset times in beats
        dur_beats: List of durations in beats
        qpm: Tempo in quarter notes per minute
        sr: Sample rate
        amplitude: Amplitude of sine waves
        fade_samples: Number of samples for fade in/out
    
    Returns:
        Synthesized audio array
    """
    if not midi_pitches or not onset_beats or not dur_beats:
        logger.warning("Empty data provided for synthesis")
        return np.array([], dtype=np.float32)
    
    if len(midi_pitches) != len(onset_beats) or len(midi_pitches) != len(dur_beats):
        logger.error("Mismatched data lengths for synthesis")
        return np.array([], dtype=np.float32)
    
    logger.info(f"Synthesizing audio: {len(midi_pitches)} notes at {qpm} BPM")
    
    try:
        # Calculate timing
        sec_per_beat = 60.0 / qpm
        total_sec = (max(onset_beats) + max(dur_beats)) * sec_per_beat if onset_beats else 1.0
        total_samples = int(total_sec * sr)
        
        # Initialize output array
        y = np.zeros(total_samples, dtype=np.float32)
        t = np.arange(total_samples) / sr
        
        # Synthesize each note
        for i, (mp, ob, db) in enumerate(zip(midi_pitches, onset_beats, dur_beats)):
            if mp <= 0:
                continue
            
            # Calculate frequency from MIDI pitch
            f = 440.0 * (2 ** ((mp - 69) / 12))
            
            # Calculate sample positions
            start_sample = int(ob * sec_per_beat * sr)
            end_sample = int((ob + db) * sec_per_beat * sr)
            
            # Ensure bounds
            start_sample = max(0, min(start_sample, total_samples))
            end_sample = max(start_sample, min(end_sample, total_samples))
            
            if start_sample >= end_sample:
                continue
            
            # Generate sine wave for this note
            note_samples = end_sample - start_sample
            note_t = np.arange(note_samples) / sr
            
            # Create sine wave with fade in/out
            sine_wave = amplitude * np.sin(2 * np.pi * f * note_t)
            
            # Apply fade in/out
            if fade_samples > 0 and note_samples > 2 * fade_samples:
                fade_in = np.linspace(0, 1, fade_samples)
                fade_out = np.linspace(1, 0, fade_samples)
                
                sine_wave[:fade_samples] *= fade_in
                sine_wave[-fade_samples:] *= fade_out
            
            # Add to output
            y[start_sample:end_sample] += sine_wave
        
        # Normalize
        max_val = np.max(np.abs(y))
        if max_val > 0:
            y = y / max_val
        
        logger.info(f"Audio synthesis completed: {len(y)} samples")
        return y
        
    except Exception as e:
        logger.error(f"Audio synthesis failed: {e}")
        return np.array([], dtype=np.float32)

def synth_piano(midi_pitches: List[int], 
                onset_beats: List[float], 
                dur_beats: List[float], 
                qpm: float, 
                sr: int = 22050,
                amplitude: float = 0.3) -> np.ndarray:
    """
    Synthesize audio from MIDI data using piano-like tones.
    
    Args:
        midi_pitches: List of MIDI pitch numbers
        onset_beats: List of onset times in beats
        dur_beats: List of durations in beats
        qpm: Tempo in quarter notes per minute
        sr: Sample rate
        amplitude: Amplitude of tones
    
    Returns:
        Synthesized audio array
    """
    if not midi_pitches or not onset_beats or not dur_beats:
        logger.warning("Empty data provided for piano synthesis")
        return np.array([], dtype=np.float32)
    
    logger.info(f"Synthesizing piano audio: {len(midi_pitches)} notes at {qpm} BPM")
    
    try:
        # Calculate timing
        sec_per_beat = 60.0 / qpm
        total_sec = (max(onset_beats) + max(dur_beats)) * sec_per_beat if onset_beats else 1.0
        total_samples = int(total_sec * sr)
        
        # Initialize output array
        y = np.zeros(total_samples, dtype=np.float32)
        t = np.arange(total_samples) / sr
        
        # Synthesize each note
        for i, (mp, ob, db) in enumerate(zip(midi_pitches, onset_beats, dur_beats)):
            if mp <= 0:
                continue
            
            # Calculate frequency from MIDI pitch
            f = 440.0 * (2 ** ((mp - 69) / 12))
            
            # Calculate sample positions
            start_sample = int(ob * sec_per_beat * sr)
            end_sample = int((ob + db) * sec_per_beat * sr)
            
            # Ensure bounds
            start_sample = max(0, min(start_sample, total_samples))
            end_sample = max(start_sample, min(end_sample, total_samples))
            
            if start_sample >= end_sample:
                continue
            
            # Generate piano-like tone (sine + harmonics with decay)
            note_samples = end_sample - start_sample
            note_t = np.arange(note_samples) / sr
            
            # Create harmonics
            fundamental = np.sin(2 * np.pi * f * note_t)
            harmonic1 = 0.5 * np.sin(2 * np.pi * f * 2 * note_t)
            harmonic2 = 0.25 * np.sin(2 * np.pi * f * 3 * note_t)
            
            # Combine harmonics
            piano_tone = fundamental + harmonic1 + harmonic2
            
            # Apply exponential decay
            decay_rate = 0.99
            decay = np.power(decay_rate, note_t * 10)
            piano_tone *= decay
            
            # Scale amplitude
            piano_tone *= amplitude
            
            # Add to output
            y[start_sample:end_sample] += piano_tone
        
        # Normalize
        max_val = np.max(np.abs(y))
        if max_val > 0:
            y = y / max_val
        
        logger.info(f"Piano synthesis completed: {len(y)} samples")
        return y
        
    except Exception as e:
        logger.error(f"Piano synthesis failed: {e}")
        return np.array([], dtype=np.float32)

def synth_audio(midi_pitches: List[int], 
                onset_beats: List[float], 
                dur_beats: List[float], 
                qpm: float, 
                sr: int = 22050,
                synth_type: str = "sine") -> np.ndarray:
    """
    Synthesize audio from MIDI data using specified synthesis method.
    
    Args:
        midi_pitches: List of MIDI pitch numbers
        onset_beats: List of onset times in beats
        dur_beats: List of durations in beats
        qpm: Tempo in quarter notes per minute
        sr: Sample rate
        synth_type: Synthesis type (sine, piano)
    
    Returns:
        Synthesized audio array
    """
    if synth_type == "sine":
        return synth_sine(midi_pitches, onset_beats, dur_beats, qpm, sr)
    elif synth_type == "piano":
        return synth_piano(midi_pitches, onset_beats, dur_beats, qpm, sr)
    else:
        logger.warning(f"Unknown synthesis type: {synth_type}, using sine")
        return synth_sine(midi_pitches, onset_beats, dur_beats, qpm, sr)
