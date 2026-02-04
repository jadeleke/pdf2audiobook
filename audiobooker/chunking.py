from __future__ import annotations

import re
from typing import Iterable, List


_ABBREVIATIONS = {
    "mr.",
    "mrs.",
    "ms.",
    "dr.",
    "prof.",
    "sr.",
    "jr.",
    "e.g.",
    "i.e.",
    "vs.",
    "etc.",
}


def _protect_abbreviations(text: str) -> str:
    for abbr in _ABBREVIATIONS:
        pattern = re.compile(re.escape(abbr), re.IGNORECASE)
        text = pattern.sub(lambda m: m.group(0).replace(".", "<prd>"), text)
    return text


def _restore_abbreviations(text: str) -> str:
    return text.replace("<prd>", ".")


def _split_sentences(text: str) -> List[str]:
    text = _protect_abbreviations(text)
    parts = re.split(r"(?<=[.!?])\s+", text)
    parts = [_restore_abbreviations(p).strip() for p in parts if p.strip()]
    return parts


def split_into_chunks(
    text: str,
    min_chars: int = 1500,
    max_chars: int = 3000,
) -> List[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: List[str] = []
    current = ""

    def flush() -> None:
        nonlocal current
        if current.strip():
            chunks.append(current.strip())
            current = ""

    for para in paragraphs:
        sentences = _split_sentences(para)
        for sentence in sentences:
            if not current:
                current = sentence
                continue
            if len(current) + len(sentence) + 1 <= max_chars:
                current = f"{current} {sentence}"
            else:
                flush()
                current = sentence
        current = f"{current}\n\n"

    flush()

    merged: List[str] = []
    buffer = ""
    for chunk in chunks:
        if not buffer:
            buffer = chunk
            continue
        if len(buffer) < min_chars:
            buffer = f"{buffer} {chunk}"
        else:
            merged.append(buffer.strip())
            buffer = chunk
    if buffer:
        merged.append(buffer.strip())
    return merged


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def estimate_minutes(words: int, wpm: int = 150) -> float:
    if wpm <= 0:
        return 0.0
    return round(words / wpm, 2)
