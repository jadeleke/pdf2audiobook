# Audiobooker

Local, production-quality PDF to audiobook CLI. Uses free, local TTS engines and writes per-chapter audio plus one merged audiobook.

## Quick start

```bash
python -m audiobooker --pdf tightcorner.pdf --out audiobook_out
```

## Requirements

- Python 3.11+
- Recommended: `ffmpeg` for mp3/m4b output and normalization
- PDF extraction: `PyMuPDF` (preferred) or `pdfplumber`
- TTS backend: Piper (default) or Coqui XTTS

### Install Python deps

```bash
python -m pip install pymupdf pdfplumber
```

### Piper (default, CPU-friendly)

Option A: pip package (installs the `piper` CLI)

```bash
python -m pip install piper-tts
```

Option B: download the Piper binary + voices

- Download a Piper release: https://github.com/rhasspy/piper/releases
- Download voices: https://huggingface.co/rhasspy/piper-voices
- Place `.onnx` models in a folder and set `PIPER_MODEL_DIR` or pass `--voice` as a path.

Default female voice: `en_US-lessac-medium`.

Example:

```bash
python -m audiobooker --pdf tightcorner.pdf --voice en_US-lessac-medium
python -m audiobooker --pdf tightcorner.pdf --voice C:\voices\en_US-lessac-medium.onnx
```

### XTTS (optional, higher quality)

```bash
python -m pip install TTS
```

XTTS v2 is heavier; GPU is recommended but CPU works. Provide a short female speaker WAV:

```bash
python -m audiobooker --pdf tightcorner.pdf --tts xtts --speaker samples/female.wav
```

### ffmpeg (recommended)

Windows:
- `winget install Gyan.FFmpeg`

macOS:
- `brew install ffmpeg`

Linux:
- `sudo apt-get install ffmpeg`

## CLI usage

```bash
python -m audiobooker --pdf tightcorner.pdf --out outdir
python -m audiobooker --pdf tightcorner.pdf --chapters auto --tts piper
python -m audiobooker --pdf tightcorner.pdf --tts xtts --speaker samples/female.wav
```

Arguments:

- `--pdf` (default: `tightcorner.pdf`)
- `--out` output dir (default: `./audiobook_out`)
- `--lang` language hint (default: `auto`)
- `--chapters` `auto|per_page|none` (default: `auto`)
- `--tts` `piper|xtts` (default: `piper`)
- `--voice` Piper model name or `.onnx` path (default: `en_US-lessac-medium`)
- `--speaker` XTTS speaker wav file (optional, recommended)
- `--speed` 0.75-1.25 (default 1.0)
- `--format` `mp3|m4b|wav` (default: mp3)
- `--normalize` (apply `ffmpeg` loudnorm when available)
- `--keep-headers` (skip header/footer removal)
- `--resume` (default: true)

## Output structure

```
outdir/
  NOTICE.txt
  chapter_index.json
  audiobook_manifest.json
  chunks/
    01_<title>/0001.wav
  01_<title>.mp3
  tightcorner.mp3
```

If `ffmpeg` is missing, the tool falls back to WAV outputs.

## Notes

- The tool prints a warning about conversion rights and creates `NOTICE.txt`.
- Per-chapter audio is created from cached chunk WAVs to support resume.

## Repository notes

- Voice models, speaker samples, and generated audio outputs are gitignored.
- Keep PDFs local (for example, `tightcorner.pdf` is ignored by default).
