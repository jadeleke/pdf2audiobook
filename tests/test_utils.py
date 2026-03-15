from audiobooker.utils import naturalize_tts_text


def test_naturalize_adds_heading_punctuation():
    text = "Chapter 1 The Beginning\n\nA paragraph without punctuation"
    shaped = naturalize_tts_text(text)
    assert "Chapter 1 The Beginning." in shaped
    assert shaped.endswith(".")
