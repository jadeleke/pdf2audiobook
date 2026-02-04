from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import List, Optional

from .audio_merge import concat_audio
from .chaptering import Chapter, build_chapters
from .chunking import split_into_chunks
from .manifest import ChunkRecord, create_manifest, load_manifest, save_manifest
from .pdf_to_text import extract_text
from .tts_piper import DEFAULT_PIPER_VOICE, synthesize as piper_synthesize
from .tts_xtts import synthesize as xtts_synthesize
from .utils import ensure_dir, ffmpeg_exists, sanitize_filename, sha256_file


DEFAULT_OUT = "audiobook_out"


def _write_notice(out_dir: Path) -> None:
    notice = out_dir / "NOTICE.txt"
    if not notice.exists():
        notice.write_text("AI-generated voice narration.\n", encoding="utf-8")


def _chapter_index(chapters: List[Chapter], out_dir: Path) -> None:
    payload = [
        {
            "title": c.title,
            "start_char": c.start_char,
            "end_char": c.end_char,
            "words": c.words,
            "est_minutes": c.est_minutes,
        }
        for c in chapters
    ]
    (out_dir / "chapter_index.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _chapters_from_pages(pages: List[str]) -> List[Chapter]:
    chapters: List[Chapter] = []
    cursor = 0
    full_text = "\n\n".join(pages)
    for idx, page in enumerate(pages, start=1):
        page = page.strip()
        if not page:
            continue
        start_char = full_text.find(page, cursor)
        end_char = start_char + len(page)
        cursor = end_char
        words = len(page.split())
        chapters.append(
            Chapter(
                title=f"Page {idx}",
                start_char=start_char,
                end_char=end_char,
                text=page,
                words=words,
                est_minutes=round(words / 150, 2) if words else 0.0,
            )
        )
    return chapters


def _detect_author(pages: List[str]) -> Optional[str]:
    if not pages:
        return None
    first = pages[0].splitlines()[:20]
    for line in first:
        if line.lower().startswith("by "):
            return line[3:].strip()
    for line in first:
        if "author" in line.lower():
            parts = line.split(":")
            if len(parts) > 1:
                return parts[-1].strip()
    return None


def _concat_wav_python(wav_paths: List[Path], output_path: Path) -> None:
    import wave

    if not wav_paths:
        return
    with wave.open(str(wav_paths[0]), "rb") as first:
        params = first.getparams()
        frames = [first.readframes(first.getnframes())]
    for wav_path in wav_paths[1:]:
        with wave.open(str(wav_path), "rb") as wf:
            if wf.getparams() != params:
                raise RuntimeError("WAV parameters mismatch; install ffmpeg for safe merging.")
            frames.append(wf.readframes(wf.getnframes()))
    with wave.open(str(output_path), "wb") as out:
        out.setparams(params)
        for chunk in frames:
            out.writeframes(chunk)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="audiobooker")
    parser.add_argument("--pdf", default="tightcorner.pdf")
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--lang", default="auto")
    parser.add_argument("--chapters", default="auto", choices=["auto", "per_page", "none"])
    parser.add_argument("--tts", default="piper", choices=["piper", "xtts"])
    parser.add_argument("--voice", default=DEFAULT_PIPER_VOICE)
    parser.add_argument("--speaker")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--format", default="mp3", choices=["mp3", "m4b", "wav"])
    parser.add_argument("--normalize", action="store_true")
    parser.add_argument("--keep-headers", action="store_true")
    parser.add_argument("--resume", action="store_true", default=True)
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"[ERROR] PDF not found: {pdf_path}")
        sys.exit(1)

    if args.speed < 0.75 or args.speed > 1.25:
        print("[ERROR] --speed must be between 0.75 and 1.25")
        sys.exit(1)

    out_dir = ensure_dir(args.out)
    _write_notice(out_dir)
    print("[WARN] Ensure you have the rights to convert this book.")

    extraction = extract_text(str(pdf_path), keep_headers=args.keep_headers)
    text = extraction.full_text

    if not text.strip():
        print("[ERROR] No text extracted from PDF.")
        sys.exit(1)

    if args.chapters == "per_page":
        chapters = _chapters_from_pages(extraction.pages)
    else:
        chapters = build_chapters(text, mode=args.chapters)
    _chapter_index(chapters, out_dir)

    settings = {
        "lang": args.lang,
        "chapters": args.chapters,
        "tts": args.tts,
        "voice": args.voice,
        "speaker": args.speaker or "",
        "speed": str(args.speed),
        "format": args.format,
        "normalize": str(args.normalize),
    }

    manifest = None
    if args.resume:
        existing = load_manifest(out_dir)
        current_hash = sha256_file(pdf_path)
        if existing and existing.pdf_hash == current_hash and existing.settings == settings:
            manifest = existing
    if manifest is None:
        manifest = create_manifest(str(pdf_path), out_dir, settings, chapters)

    chapter_outputs: List[Path] = []
    merged_output: Optional[Path] = None

    start_time = time.time()
    for chap_idx, chapter in enumerate(chapters, start=1):
        chapter_slug = sanitize_filename(chapter.title)
        chapter_dir = ensure_dir(out_dir / "chunks" / f"{chap_idx:02d}_{chapter_slug}")
        chunk_texts = split_into_chunks(chapter.text)
        chunk_paths: List[Path] = []

        print(f"[INFO] Chapter {chap_idx}/{len(chapters)}: {chapter.title}")
        for chunk_idx, chunk_text in enumerate(chunk_texts, start=1):
            chunk_path = chapter_dir / f"{chunk_idx:04d}.wav"
            chunk_paths.append(chunk_path)
            if chunk_path.exists():
                if not any(
                    c.chapter_index == chap_idx and c.chunk_index == chunk_idx
                    for c in manifest.chunks
                ):
                    manifest.chunks.append(
                        ChunkRecord(
                            chapter_index=chap_idx,
                            chunk_index=chunk_idx,
                            text_chars=len(chunk_text),
                            path=str(chunk_path),
                        )
                    )
                    save_manifest(out_dir, manifest)
                continue

            print(f"[INFO]  Chunk {chunk_idx}/{len(chunk_texts)}")
            if args.tts == "piper":
                piper_synthesize(
                    chunk_text,
                    chunk_path,
                    voice=args.voice,
                    speed=args.speed,
                )
            else:
                xtts_synthesize(
                    chunk_text,
                    chunk_path,
                    language="en" if args.lang == "auto" else args.lang,
                    speaker_wav=args.speaker,
                    speed=args.speed,
                )

            manifest.chunks.append(
                ChunkRecord(
                    chapter_index=chap_idx,
                    chunk_index=chunk_idx,
                    text_chars=len(chunk_text),
                    path=str(chunk_path),
                )
            )
            save_manifest(out_dir, manifest)

        chapter_file = out_dir / f"{chap_idx:02d}_{chapter_slug}.{args.format}"
        if args.format == "wav":
            _concat_wav_python(chunk_paths, chapter_file)
        else:
            if ffmpeg_exists():
                concat_audio(chunk_paths, chapter_file, fmt=args.format, normalize=args.normalize)
            else:
                print("[WARN] ffmpeg not available; writing WAV chapter output instead.")
                chapter_file = out_dir / f"{chap_idx:02d}_{chapter_slug}.wav"
                _concat_wav_python(chunk_paths, chapter_file)

        if str(chapter_file) not in manifest.chapter_outputs:
            manifest.chapter_outputs.append(str(chapter_file))
        save_manifest(out_dir, manifest)
        chapter_outputs.append(chapter_file)

    title = pdf_path.stem
    author = _detect_author(extraction.pages)

    if chapter_outputs:
        merged_name = out_dir / f"{title}.{args.format}"
        if args.format == "wav":
            _concat_wav_python(chapter_outputs, merged_name)
        elif ffmpeg_exists():
            durations = [c.est_minutes * 60 for c in chapters]
            concat_audio(
                chapter_outputs,
                merged_name,
                fmt=args.format,
                normalize=args.normalize,
                metadata_title=title,
                chapter_titles=[c.title for c in chapters],
                chapter_durations=durations,
            )
        else:
            merged_name = out_dir / f"{title}.wav"
            _concat_wav_python(chapter_outputs, merged_name)

        manifest.merged_output = str(merged_name)
        save_manifest(out_dir, manifest)
        merged_output = merged_name

    elapsed = time.time() - start_time
    print(f"[DONE] Completed in {elapsed:.1f}s")
    if merged_output:
        print(f"[DONE] Merged output: {merged_output}")
    if author:
        print(f"[INFO] Detected author: {author}")


if __name__ == "__main__":
    main()
