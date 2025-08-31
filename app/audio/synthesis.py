from __future__ import annotations
import numpy as np

def synth_sine(midi, onset_beats, dur_beats, qpm, sr: int = 22050) -> np.ndarray:
    sec_per_beat = 60.0 / qpm
    total_sec = (max(onset_beats) + max(dur_beats)) * sec_per_beat if onset_beats else 1.0
    y = np.zeros(int(total_sec * sr), dtype=np.float32)
    t = np.arange(len(y)) / sr
    for mp, ob, db in zip(midi, onset_beats, dur_beats):
        if mp <= 0:
            continue
        f = 440.0 * (2 ** ((mp - 69) / 12))
        start = int(ob * sec_per_beat * sr)
        end = int((ob + db) * sec_per_beat * sr)
        y[start:end] += 0.2 * np.sin(2 * np.pi * f * t[: end - start])
    return y / (np.max(np.abs(y)) + 1e-9)
