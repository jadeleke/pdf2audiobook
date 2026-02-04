from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional

from .utils import clean_tts_text, ensure_dir


DEFAULT_PIPER_VOICE = "en_US-lessac-medium"


def resolve_model(voice: str, model_dir: Optional[str] = None) -> Path:
    if voice.endswith(".onnx") and Path(voice).exists():
        return Path(voice)
    search_dirs = []
    if model_dir:
        search_dirs.append(Path(model_dir))
    env_dir = os.environ.get("PIPER_MODEL_DIR")
    if env_dir:
        search_dirs.append(Path(env_dir))
    search_dirs.append(Path.cwd() / "voices")
    search_dirs.append(Path.cwd())
    for base in search_dirs:
        candidate = base / f"{voice}.onnx"
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"Could not find Piper model for voice '{voice}'. "
        "Provide --voice as a .onnx file path or set PIPER_MODEL_DIR."
    )


def synthesize(
    text: str,
    output_path: str | Path,
    voice: str = DEFAULT_PIPER_VOICE,
    speed: float = 1.0,
    model_dir: Optional[str] = None,
) -> None:
    text = clean_tts_text(text)
    model_path = resolve_model(voice, model_dir=model_dir)
    output_path = Path(output_path)
    ensure_dir(output_path.parent)
    length_scale = max(0.5, min(2.0, 1.0 / speed))

    cmd = [
        "piper",
        "--model",
        str(model_path),
        "--output_file",
        str(output_path),
        "--length_scale",
        str(length_scale),
    ]
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8:ignore")
    env.setdefault("PYTHONUTF8", "1")
    try:
        subprocess.run(
            cmd,
            input=text,
            text=True,
            encoding="utf-8",
            check=True,
            env=env,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "Piper executable not found. Install via `pip install piper-tts` "
            "or download the Piper binary and add it to PATH."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Piper failed with exit code {exc.returncode}") from exc
