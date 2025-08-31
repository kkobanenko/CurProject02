from __future__ import annotations
import logging
import numpy as np
from typing import List, Tuple
from music21 import analysis, stream, pitch, key, meter, note

logger = logging.getLogger(__name__)

def detect_key_from_pitches(midi_pitches: List[int], 
                           method: str = "krumhansl_schmuckler") -> str:
    """
    Detect key from MIDI pitch list.
    
    Args:
        midi_pitches: List of MIDI pitch numbers
        method: Key detection method (krumhansl_schmuckler, simple)
    
    Returns:
        Key signature string (e.g., "C", "F#", "Bb")
    """
    if not midi_pitches:
        logger.warning("No pitches provided for key detection")
        return "C"
    
    # Filter out invalid MIDI pitches
    valid_pitches = [p for p in midi_pitches if 0 <= p <= 127]
    if not valid_pitches:
        logger.warning("No valid MIDI pitches found")
        return "C"
    
    logger.debug(f"Detecting key from {len(valid_pitches)} pitches")
    
    try:
        if method == "krumhansl_schmuckler":
            return _detect_key_krumhansl_schmuckler(valid_pitches)
        elif method == "simple":
            return _detect_key_simple(valid_pitches)
        else:
            logger.warning(f"Unknown key detection method: {method}, using krumhansl_schmuckler")
            return _detect_key_krumhansl_schmuckler(valid_pitches)
    except Exception as e:
        logger.error(f"Key detection failed: {e}")
        return "C"

def _detect_key_krumhansl_schmuckler(midi_pitches: List[int]) -> str:
    """Detect key using Krumhansl-Schmuckler algorithm."""
    s = stream.Stream()
    
    # Limit to first 512 pitches to avoid memory issues
    pitches_to_analyze = midi_pitches[:512]
    
    for mp in pitches_to_analyze:
        n = note.Note()
        n.pitch = pitch.Pitch(midi=mp)
        s.append(n)
    
    k = analysis.discrete.KrumhanslSchmuckler().getSolution(s)
    key_str = str(k)
    
    # Extract just the key name (e.g., "A" from "A major")
    if " " in key_str:
        key_str = key_str.split(" ")[0]
    
    logger.debug(f"Krumhansl-Schmuckler key detection result: {key_str}")
    return key_str

def _detect_key_simple(midi_pitches: List[int]) -> str:
    """Simple key detection based on pitch class distribution."""
    # Convert MIDI pitches to pitch classes (0-11)
    pitch_classes = [p % 12 for p in midi_pitches]
    
    # Count occurrences of each pitch class
    pitch_class_counts = np.zeros(12)
    for pc in pitch_classes:
        pitch_class_counts[pc] += 1
    
    # Find the most common pitch class
    most_common_pc = np.argmax(pitch_class_counts)
    
    # Map pitch class to key name
    key_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    key_str = key_names[most_common_pc]
    
    logger.debug(f"Simple key detection result: {key_str}")
    return key_str

def default_time_signature() -> str:
    """Return default time signature."""
    return "4/4"

def parse_time_signature(time_sig_str: str) -> Tuple[int, int]:
    """
    Parse time signature string to numerator and denominator.
    
    Args:
        time_sig_str: Time signature string (e.g., "4/4", "3/4")
    
    Returns:
        Tuple of (numerator, denominator)
    """
    try:
        parts = time_sig_str.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid time signature format: {time_sig_str}")
        
        numerator = int(parts[0])
        denominator = int(parts[1])
        
        if numerator <= 0 or denominator <= 0:
            raise ValueError(f"Invalid time signature values: {time_sig_str}")
        
        return numerator, denominator
    except Exception as e:
        logger.error(f"Failed to parse time signature {time_sig_str}: {e}")
        return 4, 4

def validate_time_signature(numerator: int, denominator: int) -> bool:
    """
    Validate time signature values.
    
    Args:
        numerator: Time signature numerator
        denominator: Time signature denominator
    
    Returns:
        True if valid, False otherwise
    """
    if numerator <= 0 or denominator <= 0:
        return False
    
    # Check if denominator is a power of 2
    if not (denominator & (denominator - 1) == 0):
        return False
    
    return True

def get_common_time_signatures() -> List[str]:
    """Return list of common time signatures."""
    return ["2/4", "3/4", "4/4", "6/8", "3/8", "2/2"]
