from __future__ import annotations
import os
import logging
import subprocess
from typing import List, Optional, Tuple
import numpy as np
from music21 import stream, note, meter, key as m21key, tempo as m21tempo, duration, clef
from app.settings import settings

logger = logging.getLogger(__name__)

def f0_to_midi(f0_hz: List[float]) -> List[int]:
    """
    Convert F0 frequencies to MIDI pitch numbers.
    
    Args:
        f0_hz: List of F0 frequencies in Hz
    
    Returns:
        List of MIDI pitch numbers (0-127, 0 = rest)
    """
    if not f0_hz:
        return []
    
    try:
        import librosa
        midi = librosa.hz_to_midi(np.maximum(1e-6, f0_hz))
        midi = np.where(np.isfinite(midi), midi, 0.0)
        midi = np.clip(midi, 0, 127)
        
        logger.debug(f"Converted {len(f0_hz)} F0 values to MIDI pitches")
        return midi.astype(int).tolist()
        
    except Exception as e:
        logger.error(f"F0 to MIDI conversion failed: {e}")
        return [0] * len(f0_hz)

def build_score(midi_pitches: List[int], 
               onset_beats: List[float], 
               dur_beats: List[float], 
               key_signature: str = "C",
               time_signature: str = "4/4",
               qpm: float = 120.0,
               title: str = "Extracted Melody") -> stream.Score:
    """
    Build a music21 Score from MIDI data.
    
    Args:
        midi_pitches: List of MIDI pitch numbers
        onset_beats: List of onset times in beats
        dur_beats: List of durations in beats
        key_signature: Key signature string
        time_signature: Time signature string
        qpm: Tempo in quarter notes per minute
        title: Score title
    
    Returns:
        music21 Score object
    """
    if not midi_pitches or not onset_beats or not dur_beats:
        logger.warning("Empty data provided for score building")
        return stream.Score()
    
    if len(midi_pitches) != len(onset_beats) or len(midi_pitches) != len(dur_beats):
        logger.error("Mismatched data lengths for score building")
        return stream.Score()
    
    logger.info(f"Building score: {len(midi_pitches)} notes, key={key_signature}, time={time_signature}, tempo={qpm}")
    
    try:
        # Create score and part
        sc = stream.Score()
        part = stream.Part()
        
        # Add metadata
        sc.metadata = stream.Metadata()
        sc.metadata.title = title
        
        # Add tempo marking
        part.append(m21tempo.MetronomeMark(number=qpm))
        
        # Add time signature
        try:
            ts = meter.TimeSignature(time_signature)
            part.append(ts)
        except Exception as e:
            logger.warning(f"Failed to add time signature {time_signature}: {e}")
            part.append(meter.TimeSignature("4/4"))
        
        # Add key signature
        try:
            k = m21key.Key(key_signature)
            part.append(k)
        except Exception as e:
            logger.warning(f"Failed to add key signature {key_signature}: {e}")
            part.append(m21key.Key("C"))
        
        # Add clef
        part.append(clef.TrebleClef())
        
        # Add notes and rests
        for i, (mp, ob, db) in enumerate(zip(midi_pitches, onset_beats, dur_beats)):
            if mp <= 0 or db <= 0:
                # Add rest
                n = note.Rest()
            else:
                # Add note
                try:
                    n = note.Note(mp)
                except Exception as e:
                    logger.warning(f"Failed to create note with pitch {mp}: {e}")
                    n = note.Rest()
            
            # Set duration
            try:
                d = duration.Duration(quarterLength=db)
                n.duration = d
            except Exception as e:
                logger.warning(f"Failed to set duration {db}: {e}")
                n.duration = duration.Duration(quarterLength=1.0)
            
            part.append(n)
        
        sc.insert(0, part)
        logger.info(f"Score built successfully: {len(midi_pitches)} events")
        return sc
        
    except Exception as e:
        logger.error(f"Score building failed: {e}")
        return stream.Score()

def export_musicxml(score: stream.Score, out_path: str) -> str:
    """
    Export music21 Score to MusicXML file.
    
    Args:
        score: music21 Score object
        out_path: Output file path
    
    Returns:
        Output file path
    """
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        
        # Export to MusicXML
        score.write("musicxml", fp=out_path)
        
        logger.info(f"MusicXML exported to: {out_path}")
        return out_path
        
    except Exception as e:
        logger.error(f"MusicXML export failed: {e}")
        raise

def render_to_pdf_png(musicxml_path: str, 
                     out_pdf: Optional[str] = None, 
                     out_png: Optional[str] = None) -> List[str]:
    """
    Render MusicXML to PDF and/or PNG using external tools.
    
    Args:
        musicxml_path: Input MusicXML file path
        out_pdf: Output PDF file path (optional)
        out_png: Output PNG file path (optional)
    
    Returns:
        List of successfully created output files
    """
    if not os.path.exists(musicxml_path):
        logger.error(f"MusicXML file not found: {musicxml_path}")
        return []
    
    output_files = []
    
    if settings.renderer == "mscore":
        # Try MuseScore
        musescore_commands = ["mscore", "musescore3", "musescore4"]
        
        for cmd in musescore_commands:
            try:
                if out_pdf:
                    logger.debug(f"Rendering PDF with {cmd}")
                    subprocess.run([cmd, "-o", out_pdf, musicxml_path], 
                                 check=True, timeout=settings.render_timeout_sec,
                                 capture_output=True)
                    output_files.append(out_pdf)
                    logger.info(f"PDF rendered: {out_pdf}")
                
                if out_png:
                    logger.debug(f"Rendering PNG with {cmd}")
                    subprocess.run([cmd, "-o", out_png, musicxml_path], 
                                 check=True, timeout=settings.render_timeout_sec,
                                 capture_output=True)
                    output_files.append(out_png)
                    logger.info(f"PNG rendered: {out_png}")
                
                # If we get here, rendering was successful
                break
                
            except subprocess.TimeoutExpired:
                logger.warning(f"{cmd} timed out after {settings.render_timeout_sec}s")
                continue
            except subprocess.CalledProcessError as e:
                logger.warning(f"{cmd} failed: {e}")
                continue
            except FileNotFoundError:
                logger.debug(f"{cmd} not found")
                continue
    
    elif settings.renderer == "verovio":
        # Try Verovio
        try:
            if out_png:
                logger.debug("Rendering PNG with verovio")
                subprocess.run(["verovio", "--format", "png", "--output", out_png, musicxml_path],
                             check=True, timeout=settings.render_timeout_sec,
                             capture_output=True)
                output_files.append(out_png)
                logger.info(f"PNG rendered: {out_png}")
            
            if out_pdf:
                logger.debug("Rendering PDF with verovio")
                subprocess.run(["verovio", "--format", "pdf", "--output", out_pdf, musicxml_path],
                             check=True, timeout=settings.render_timeout_sec,
                             capture_output=True)
                output_files.append(out_pdf)
                logger.info(f"PDF rendered: {out_pdf}")
                
        except subprocess.TimeoutExpired:
            logger.warning(f"verovio timed out after {settings.render_timeout_sec}s")
        except subprocess.CalledProcessError as e:
            logger.warning(f"verovio failed: {e}")
        except FileNotFoundError:
            logger.warning("verovio not found")
    
    else:
        logger.info(f"Renderer set to '{settings.renderer}', skipping PDF/PNG generation")
    
    return output_files

def create_score_from_f0(f0_hz: List[float], 
                        times: List[float],
                        tempo_bpm: float = 120.0,
                        key_signature: str = "C",
                        time_signature: str = "4/4",
                        title: str = "Extracted Melody") -> stream.Score:
    """
    Create a complete score from F0 data.
    
    Args:
        f0_hz: F0 frequencies in Hz
        times: Time positions in seconds
        tempo_bpm: Tempo in BPM
        key_signature: Key signature
        time_signature: Time signature
        title: Score title
    
    Returns:
        music21 Score object
    """
    if not f0_hz or not times:
        logger.warning("Empty F0 data provided")
        return stream.Score()
    
    # Convert F0 to MIDI
    midi_pitches = f0_to_midi(f0_hz)
    
    # Convert times to beats
    from app.audio.quantize import times_to_beats
    beats = times_to_beats(np.array(times), tempo_bpm)
    
    # Calculate durations (simple approach)
    if len(beats) > 1:
        durations = np.diff(beats)
        durations = np.append(durations, 1.0)  # Last note gets 1 beat duration
    else:
        durations = np.array([1.0])
    
    # Build score
    return build_score(
        midi_pitches=midi_pitches,
        onset_beats=beats.tolist(),
        dur_beats=durations.tolist(),
        key_signature=key_signature,
        time_signature=time_signature,
        qpm=tempo_bpm,
        title=title
    )
