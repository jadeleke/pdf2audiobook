import json
from pathlib import Path

from audiobooker.manifest import create_manifest, load_manifest


def test_manifest_roundtrip(tmp_path: Path):
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"dummy")
    chapters = []
    settings = {"tts": "piper"}
    manifest = create_manifest(str(pdf), tmp_path, settings, chapters)
    loaded = load_manifest(tmp_path)
    assert loaded is not None
    assert loaded.pdf_hash == manifest.pdf_hash
    assert loaded.settings == settings
