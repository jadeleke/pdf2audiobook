from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, List


@dataclass
class ExtractedText:
    pages: List[str]
    full_text: str


def _clean_page_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _dehyphenate(text: str) -> str:
    return re.sub(r"(\w)-\n(\w)", r"\1\2", text)


def _remove_isolated_page_numbers(lines: Iterable[str]) -> List[str]:
    cleaned: List[str] = []
    for line in lines:
        stripped = line.strip()
        if re.fullmatch(r"\d{1,4}", stripped):
            continue
        cleaned.append(line)
    return cleaned


def _remove_headers_footers(pages: List[str]) -> List[str]:
    line_counts = Counter()
    page_lines = []
    for page in pages:
        lines = [l for l in page.splitlines() if l.strip()]
        page_lines.append(lines)
        line_counts.update(set(lines))
    threshold = max(2, int(len(pages) * 0.6))
    repeated = {line for line, count in line_counts.items() if count >= threshold}
    cleaned_pages = []
    for lines in page_lines:
        kept = [l for l in lines if l not in repeated]
        kept = _remove_isolated_page_numbers(kept)
        cleaned_pages.append("\n".join(kept).strip())
    return cleaned_pages


def _extract_with_fitz(pdf_path: str) -> List[str]:
    import fitz  # type: ignore

    doc = fitz.open(pdf_path)
    pages = []
    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text()
        text = _clean_page_text(text)
        pages.append(text)
    return pages


def _extract_with_pdfplumber(pdf_path: str) -> List[str]:
    import pdfplumber  # type: ignore

    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            text = _clean_page_text(text)
            pages.append(text)
    return pages


def extract_text(pdf_path: str, keep_headers: bool = False) -> ExtractedText:
    pages: List[str]
    try:
        pages = _extract_with_fitz(pdf_path)
    except Exception:
        pages = _extract_with_pdfplumber(pdf_path)

    pages = [_dehyphenate(p) for p in pages]
    if not keep_headers:
        pages = _remove_headers_footers(pages)
    full = "\n\n".join(p for p in pages if p.strip())
    full = re.sub(r"\n{3,}", "\n\n", full).strip()
    return ExtractedText(pages=pages, full_text=full)
