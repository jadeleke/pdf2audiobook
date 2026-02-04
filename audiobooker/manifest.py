from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .chaptering import Chapter
from .utils import sha256_file


@dataclass
class ChunkRecord:
    chapter_index: int
    chunk_index: int
    text_chars: int
    path: str


@dataclass
class Manifest:
    pdf_path: str
    pdf_hash: str
    settings: Dict[str, str]
    chapters: List[Dict]
    chunks: List[ChunkRecord]
    chapter_outputs: List[str]
    merged_output: Optional[str]

    def to_json(self) -> str:
        payload = asdict(self)
        payload["chunks"] = [asdict(c) for c in self.chunks]
        return json.dumps(payload, indent=2)


def manifest_path(out_dir: str | Path) -> Path:
    return Path(out_dir) / "audiobook_manifest.json"


def load_manifest(out_dir: str | Path) -> Optional[Manifest]:
    path = manifest_path(out_dir)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    chunks = [ChunkRecord(**c) for c in data.get("chunks", [])]
    return Manifest(
        pdf_path=data["pdf_path"],
        pdf_hash=data["pdf_hash"],
        settings=data.get("settings", {}),
        chapters=data.get("chapters", []),
        chunks=chunks,
        chapter_outputs=data.get("chapter_outputs", []),
        merged_output=data.get("merged_output"),
    )


def create_manifest(
    pdf_path: str,
    out_dir: str | Path,
    settings: Dict[str, str],
    chapters: List[Chapter],
) -> Manifest:
    data = Manifest(
        pdf_path=pdf_path,
        pdf_hash=sha256_file(pdf_path),
        settings=settings,
        chapters=[
            {
                "title": c.title,
                "start_char": c.start_char,
                "end_char": c.end_char,
                "words": c.words,
                "est_minutes": c.est_minutes,
            }
            for c in chapters
        ],
        chunks=[],
        chapter_outputs=[],
        merged_output=None,
    )
    save_manifest(out_dir, data)
    return data


def save_manifest(out_dir: str | Path, manifest: Manifest) -> None:
    path = manifest_path(out_dir)
    path.write_text(manifest.to_json(), encoding="utf-8")
