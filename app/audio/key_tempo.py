from __future__ import annotations
from music21 import analysis, stream, pitch

def detect_key_from_pitches(midi_pitches: list[int]) -> str:
    s = stream.Stream()
    for mp in midi_pitches[:512]:
        n = pitch.Pitch()
        n.midi = mp
        s.append(n)
    k = analysis.discrete.KrumhanslSchmuckler().getSolution(s)
    return str(k)

def default_time_signature() -> str:
    return "4/4"
