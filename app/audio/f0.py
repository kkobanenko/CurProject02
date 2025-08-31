from __future__ import annotations
import numpy as np
import librosa

try:
    import torchcrepe  # type: ignore
except Exception:  # pragma: no cover
    torchcrepe = None

def estimate_f0_pyin(y: np.ndarray, sr: int, frame_length: int = 2048, hop_length: int = 160):
    f0, voiced_flag, _ = librosa.pyin(
        y,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C7"),
        frame_length=frame_length,
        hop_length=hop_length,
    )
    t = librosa.frames_to_time(np.arange(len(f0)), sr=sr, hop_length=hop_length)
    f0_hz = np.where(np.isnan(f0), 0.0, f0)
    return t, f0_hz.astype(np.float32), voiced_flag.astype(bool)

def estimate_f0_torchcrepe(y: np.ndarray, sr: int, hop_seconds: float = 0.01):
    if torchcrepe is None:
        raise RuntimeError("torchcrepe не установлен")
    import torch  # lazy
    device = "cpu"
    x = torch.tensor(y, dtype=torch.float32)[None, None, :]
    f0 = torchcrepe.predict(
        x, sr, int(sr * hop_seconds),
        fmin=50, fmax=1100,
        model="full", batch_size=1024, device=device, return_periodicity=False,
    )[0]
    f0 = f0.numpy()
    t = np.arange(len(f0)) * hop_seconds
    voiced = f0 > 0
    return t.astype(np.float32), f0.astype(np.float32), voiced
