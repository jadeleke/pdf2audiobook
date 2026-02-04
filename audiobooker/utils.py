from __future__ import annotations

import hashlib
import os
import re
import shutil
from pathlib import Path


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def ffmpeg_exists() -> bool:
    return shutil.which("ffmpeg") is not None


def sanitize_filename(text: str, max_len: int = 80) -> str:
    cleaned = re.sub(r"[^\w\s\-\.]", "", text, flags=re.UNICODE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        cleaned = "chapter"
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].rstrip()
    return cleaned.replace(" ", "_")


def safe_remove(path: str | Path) -> None:
    try:
        os.remove(path)
    except FileNotFoundError:
        return


def clean_tts_text(text: str) -> str:
    return text.encode("utf-8", "ignore").decode("utf-8")
