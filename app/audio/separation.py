from __future__ import annotations
import os
import subprocess
import tempfile

def separate_vocals_demucs(input_path: str, output_dir: str) -> str:
    """
    Разделение источников через Demucs (htdemucs).
    Возвращает путь к вокальному стему (wav), если он найден; иначе выбрасывает исключение.
    """
    os.makedirs(output_dir, exist_ok=True)
    # Пример: python -m demucs.separate -n htdemucs -о <out_dir> <input>
    cmd = ["python", "-m", "demucs.separate", "-n", "htdemucs", "-o", output_dir, input_path]
    subprocess.run(cmd, check=True)
    base = os.path.splitext(os.path.basename(input_path))[0]
    # demucs кладёт файлы: <out_dir>/<model>/<basename>/*.wav
    cand = os.path.join(output_dir, "htdemucs", base, "vocals.wav")
    if not os.path.exists(cand):
        for name in ("vocals.wav", "vocals.wav", f"{base}.vocals.wav"):
            p = os.path.join(output_dir, "htdemucs", base, name)
            if os.path.exists(p):
                cand = p
                break
    if not os.path.exists(cand):
        raise FileNotFoundError("Demucs: не найден вокальный STEM.")
    return cand
