from pathlib import Path

from audiobooker.cli import _interleave_with_pause


def test_interleave_with_pause_inserts_between_items():
    p1 = Path("a.wav")
    p2 = Path("b.wav")
    pause = Path("pause.wav")
    result = _interleave_with_pause([p1, p2], pause)
    assert result == [p1, pause, p2]


def test_interleave_with_pause_single_item_no_change():
    p1 = Path("a.wav")
    pause = Path("pause.wav")
    result = _interleave_with_pause([p1], pause)
    assert result == [p1]
