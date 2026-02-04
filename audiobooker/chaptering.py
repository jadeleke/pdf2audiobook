from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from .chunking import estimate_minutes, word_count


@dataclass
class Chapter:
    title: str
    start_char: int
    end_char: int
    text: str
    words: int
    est_minutes: float


_HEADING_PATTERNS = [
    re.compile(r"^\s*chapter\s+\d+[\.\: ]", re.IGNORECASE),
    re.compile(r"^\s*chapter\s+[ivxlcdm]+[\.\: ]", re.IGNORECASE),
    re.compile(r"^\s*chapter\s+[a-z]+[\.\: ]", re.IGNORECASE),
    re.compile(r"^\s*part\s+[ivxlcdm]+[\.\: ]", re.IGNORECASE),
    re.compile(r"^\s*part\s+\d+[\.\: ]", re.IGNORECASE),
    re.compile(r"^\s*\d+\.\s+\S+"),
]


def _is_heading(line: str) -> bool:
    if len(line) > 80:
        return False
    for pattern in _HEADING_PATTERNS:
        if pattern.match(line):
            return True
    return False


def detect_chapters(text: str) -> List[Chapter]:
    lines = text.splitlines()
    offsets = []
    cursor = 0
    for line in lines:
        offsets.append(cursor)
        cursor += len(line) + 1

    headings = []
    for idx, line in enumerate(lines):
        if _is_heading(line.strip()):
            headings.append((idx, line.strip()))

    if not headings:
        return []

    chapters: List[Chapter] = []
    for i, (line_idx, title) in enumerate(headings):
        start_char = offsets[line_idx]
        if i + 1 < len(headings):
            end_char = offsets[headings[i + 1][0]]
        else:
            end_char = len(text)
        chapter_text = text[start_char:end_char].strip()
        words = word_count(chapter_text)
        chapters.append(
            Chapter(
                title=title,
                start_char=start_char,
                end_char=end_char,
                text=chapter_text,
                words=words,
                est_minutes=estimate_minutes(words),
            )
        )
    return chapters


def segment_by_word_count(text: str, min_words: int = 1500, max_words: int = 3000) -> List[Chapter]:
    words = re.findall(r"\b\w+\b", text)
    if not words:
        return []
    chapters: List[Chapter] = []
    current_words: List[str] = []
    start_char = 0
    cursor = 0
    word_iter = re.finditer(r"\b\w+\b", text)
    word_positions = [(m.start(), m.end()) for m in word_iter]

    for idx, (start, end) in enumerate(word_positions):
        current_words.append(text[start:end])
        if len(current_words) >= max_words:
            end_char = end
            chapter_text = text[start_char:end_char].strip()
            chapter_words = word_count(chapter_text)
            chapters.append(
                Chapter(
                    title=f"Section {len(chapters) + 1}",
                    start_char=start_char,
                    end_char=end_char,
                    text=chapter_text,
                    words=chapter_words,
                    est_minutes=estimate_minutes(chapter_words),
                )
            )
            start_char = end_char
            current_words = []
        cursor = idx

    if start_char < len(text):
        chapter_text = text[start_char:].strip()
        chapter_words = word_count(chapter_text)
        if chapter_words:
            chapters.append(
                Chapter(
                    title=f"Section {len(chapters) + 1}",
                    start_char=start_char,
                    end_char=len(text),
                    text=chapter_text,
                    words=chapter_words,
                    est_minutes=estimate_minutes(chapter_words),
                )
            )
    return chapters


def build_chapters(text: str, mode: str) -> List[Chapter]:
    if mode == "none":
        words = word_count(text)
        return [
            Chapter(
                title="Full Book",
                start_char=0,
                end_char=len(text),
                text=text,
                words=words,
                est_minutes=estimate_minutes(words),
            )
        ]
    if mode == "per_page":
        parts = text.split("\n\n")
        chapters: List[Chapter] = []
        cursor = 0
        for idx, part in enumerate(parts, start=1):
            part = part.strip()
            if not part:
                continue
            start_char = text.find(part, cursor)
            end_char = start_char + len(part)
            cursor = end_char
            words = word_count(part)
            chapters.append(
                Chapter(
                    title=f"Page {idx}",
                    start_char=start_char,
                    end_char=end_char,
                    text=part,
                    words=words,
                    est_minutes=estimate_minutes(words),
                )
            )
        return chapters

    detected = detect_chapters(text)
    if detected:
        return detected
    return segment_by_word_count(text)
