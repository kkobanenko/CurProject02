from __future__ import annotations
import os
import logging
import subprocess
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)

def separate_vocals_demucs(input_path: str, output_dir: str, model: str = "htdemucs") -> str:
    """
    Разделение источников через Demucs.
    
    Args:
        input_path: Путь к входному аудио файлу
        output_dir: Директория для сохранения результатов
        model: Модель Demucs (htdemucs, htdemucs_ft, mdx_extra, mdx_extra_q)
    
    Returns:
        Путь к вокальному стему (wav)
    
    Raises:
        FileNotFoundError: Если входной файл не найден
        subprocess.CalledProcessError: Если Demucs завершился с ошибкой
        FileNotFoundError: Если вокальный STEM не найден
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    os.makedirs(output_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(input_path))[0]
    
    logger.info(f"Starting source separation with Demucs: model={model}, input={input_path}")
    
    try:
        # Run Demucs separation
        cmd = [
            "python", "-m", "demucs.separate",
            "-n", model,
            "-o", output_dir,
            "--two-stems=vocals",  # Only separate vocals
            input_path
        ]
        
        logger.debug(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.debug(f"Demucs stdout: {result.stdout}")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Demucs failed: {e}")
        logger.error(f"Demucs stderr: {e.stderr}")
        raise
    
    # Look for vocals file
    possible_paths = [
        os.path.join(output_dir, model, base, "vocals.wav"),
        os.path.join(output_dir, model, base, f"{base}.vocals.wav"),
        os.path.join(output_dir, model, base, "vocals_0.wav"),
    ]
    
    vocals_path = None
    for path in possible_paths:
        if os.path.exists(path):
            vocals_path = path
            break
    
    if vocals_path is None:
        logger.error(f"Vocals file not found. Checked paths: {possible_paths}")
        raise FileNotFoundError("Demucs: не найден вокальный STEM")
    
    logger.info(f"Source separation completed: vocals_path={vocals_path}")
    return vocals_path

def separate_vocals_spleeter(input_path: str, output_dir: str) -> str:
    """
    Разделение источников через Spleeter (2stems).
    
    Args:
        input_path: Путь к входному аудио файлу
        output_dir: Директория для сохранения результатов
    
    Returns:
        Путь к вокальному стему (wav)
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    os.makedirs(output_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(input_path))[0]
    
    logger.info(f"Starting source separation with Spleeter: input={input_path}")
    
    try:
        # Run Spleeter separation
        cmd = [
            "spleeter", "separate",
            "-p", "spleeter:2stems",
            "-o", output_dir,
            input_path
        ]
        
        logger.debug(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.debug(f"Spleeter stdout: {result.stdout}")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Spleeter failed: {e}")
        logger.error(f"Spleeter stderr: {e.stderr}")
        raise
    
    # Look for vocals file
    vocals_path = os.path.join(output_dir, base, "vocals.wav")
    
    if not os.path.exists(vocals_path):
        logger.error(f"Vocals file not found: {vocals_path}")
        raise FileNotFoundError("Spleeter: не найден вокальный STEM")
    
    logger.info(f"Source separation completed: vocals_path={vocals_path}")
    return vocals_path

def separate_sources(input_path: str, output_dir: str, method: str = "demucs") -> str:
    """
    Разделение источников с выбором метода.
    
    Args:
        input_path: Путь к входному аудио файлу
        output_dir: Директория для сохранения результатов
        method: Метод разделения (demucs, spleeter)
    
    Returns:
        Путь к вокальному стему
    """
    if method == "demucs":
        return separate_vocals_demucs(input_path, output_dir)
    elif method == "spleeter":
        return separate_vocals_spleeter(input_path, output_dir)
    else:
        raise ValueError(f"Unknown separation method: {method}. Supported: demucs, spleeter")
