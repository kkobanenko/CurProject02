import numpy as np
from app.audio.f0 import estimate_f0_pyin

def test_f0_basic():
    sr = 22050
    t = np.linspace(0, 1.0, int(sr), endpoint=False)
    y = 0.2 * np.sin(2*np.pi*440*t)  # A4
    times, f0, voiced = estimate_f0_pyin(y, sr)
    assert (f0 > 0).sum() > 10
