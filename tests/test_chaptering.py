from audiobooker.chaptering import build_chapters, detect_chapters


def test_detect_chapters_basic():
    text = "\n".join(
        [
            "CHAPTER 1 The Beginning",
            "This is the first chapter.",
            "CHAPTER 2 The Middle",
            "This is the second chapter.",
        ]
    )
    chapters = detect_chapters(text)
    assert len(chapters) == 2
    assert chapters[0].title.lower().startswith("chapter 1")
    assert chapters[1].title.lower().startswith("chapter 2")


def test_build_chapters_fallback_segment():
    text = "word " * 4000
    chapters = build_chapters(text, mode="auto")
    assert len(chapters) >= 2
