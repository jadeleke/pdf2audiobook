from audiobooker.chunking import split_into_chunks


def test_chunking_respects_abbreviations():
    text = "Dr. Smith went to the store. He bought milk."
    chunks = split_into_chunks(text, min_chars=10, max_chars=100)
    assert len(chunks) == 1
    assert "Dr. Smith" in chunks[0]
