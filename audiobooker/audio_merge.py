from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable, List, Optional

from .utils import ensure_dir, ffmpeg_exists, safe_remove


def _write_concat_list(paths: Iterable[Path], list_path: Path) -> None:
    lines = [f"file '{p.resolve().as_posix()}'" for p in paths]
    list_path.write_text("\n".join(lines), encoding="utf-8")


def _write_ffmetadata(
    chapter_titles: List[str],
    chapter_durations: List[float],
    output_path: Path,
    title: Optional[str] = None,
) -> None:
    lines = [";FFMETADATA1"]
    if title:
        lines.append(f"title={title}")
    start = 0
    for name, duration in zip(chapter_titles, chapter_durations):
        end = start + int(duration * 1000)
        lines.extend(
            [
                "[CHAPTER]",
                "TIMEBASE=1/1000",
                f"START={start}",
                f"END={end}",
                f"title={name}",
            ]
        )
        start = end
    output_path.write_text("\n".join(lines), encoding="utf-8")


def concat_audio(
    input_wavs: List[Path],
    output_path: Path,
    fmt: str = "mp3",
    normalize: bool = False,
    metadata_title: Optional[str] = None,
    chapter_titles: Optional[List[str]] = None,
    chapter_durations: Optional[List[float]] = None,
) -> Path:
    if not ffmpeg_exists():
        raise RuntimeError("ffmpeg not found in PATH.")

    ensure_dir(output_path.parent)
    list_path = output_path.parent / "concat_list.txt"
    _write_concat_list(input_wavs, list_path)
    temp_wav = output_path.parent / "merged_temp.wav"
    concat_cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_path),
        "-c:a",
        "pcm_s16le",
        str(temp_wav),
    ]
    subprocess.run(concat_cmd, check=True)

    args = [
        "ffmpeg",
        "-y",
        "-i",
        str(temp_wav),
    ]

    metadata_path: Optional[Path] = None
    if fmt == "m4b" and chapter_titles and chapter_durations:
        metadata_path = output_path.parent / "chapters_metadata.txt"
        _write_ffmetadata(chapter_titles, chapter_durations, metadata_path, title=metadata_title)
        args.extend(["-i", str(metadata_path), "-map_metadata", "1"])

    if metadata_title:
        args.extend(["-metadata", f"title={metadata_title}"])

    if normalize:
        args.extend(["-af", "loudnorm"])

    if fmt == "mp3":
        args.extend(["-codec:a", "libmp3lame", "-b:a", "192k"])
    elif fmt == "m4b":
        args.extend(["-codec:a", "aac", "-b:a", "192k"])
    else:
        args.extend(["-codec:a", "pcm_s16le"])

    args.append(str(output_path))
    subprocess.run(args, check=True)

    safe_remove(temp_wav)
    safe_remove(list_path)
    if metadata_path:
        safe_remove(metadata_path)
    return output_path
