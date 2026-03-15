from audiobooker.chunking import split_into_chunks


def test_chunking_respects_abbreviations():
    text = "Dr. Smith went to the store. He bought milk."
    chunks = split_into_chunks(text, min_chars=10, max_chars=100)
    assert len(chunks) == 1
    assert "Dr. Smith" in chunks[0]


def test_chunking_preserves_paragraph_gap_when_merging():
    text = "First paragraph sentence one.\n\nSecond paragraph sentence one."
    chunks = split_into_chunks(text, min_chars=300, max_chars=500, preserve_paragraph_gaps=True)
    assert len(chunks) == 1
    assert "\n\n" in chunks[0]
