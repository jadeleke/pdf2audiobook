from __future__ import annotations

from pathlib import Path
from typing import Optional

from .utils import clean_tts_text


def synthesize(
    text: str,
    output_path: str | Path,
    language: str = "en",
    speaker_wav: Optional[str] = None,
    speed: float = 1.0,
) -> None:
    text = clean_tts_text(text)
    try:
        from TTS.api import TTS  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "Coqui TTS not installed. Install with `pip install TTS`."
        ) from exc

    tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")
    if speaker_wav is None:
        if getattr(tts, "speakers", None):
            speaker = tts.speakers[0]
            tts.tts_to_file(text=text, file_path=str(output_path), speaker=speaker, speed=speed)
            return
        raise RuntimeError("XTTS requires --speaker WAV for voice cloning.")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tts.tts_to_file(
        text=text,
        file_path=str(output_path),
        speaker_wav=speaker_wav,
        language=language,
        speed=speed,
    )
