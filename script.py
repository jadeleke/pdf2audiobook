import fitz  # PyMuPDF
import os
import re
from openai import OpenAI

# ==========================
# CONFIGURATION
# ==========================

PDF_PATH = "tightcorner.pdf"
OUTPUT_AUDIO = "audiobook.mp3"

VOICE = "alloy"          # Sweet, smooth female-style voice
MODEL = "gpt-4o-mini-tts"

CHUNK_SIZE = 3000        # Characters per TTS request (safe limit)

client = OpenAI()

# ==========================
# PDF TEXT EXTRACTION
# ==========================

def extract_text_from_pdf(pdf_path):
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = fitz.open(pdf_path)
    pages_text = []

    print(f"[INFO] Extracting text from {len(doc)} pages...")

    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text()
        text = clean_text(text)

        if text.strip():
            pages_text.append(text)

        print(f"[INFO] Page {i + 1}/{len(doc)} extracted")

    return "\n\n".join(pages_text)

# ==========================
# TEXT CLEANING
# ==========================

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'Page \d+', '', text)
    text = text.replace('\u00a0', ' ')
    return text.strip()

# ==========================
# TEXT CHUNKING
# ==========================

def split_text(text, max_length):
    chunks = []
    current = ""

    for paragraph in text.split("\n"):
        if len(current) + len(paragraph) < max_length:
            current += paragraph + "\n"
        else:
            chunks.append(current.strip())
            current = paragraph + "\n"

    if current.strip():
        chunks.append(current.strip())

    return chunks

# ==========================
# OPENAI TEXT TO SPEECH
# ==========================

def generate_audiobook(text, output_file):
    chunks = split_text(text, CHUNK_SIZE)

    print(f"[INFO] Converting text to speech ({len(chunks)} chunks)...")

    with open(output_file, "wb") as audio_file:
        for index, chunk in enumerate(chunks, start=1):
            print(f"[INFO] Generating audio chunk {index}/{len(chunks)}")

            response = client.audio.speech.create(
                model=MODEL,
                voice=VOICE,
                input=chunk
            )

            audio_file.write(response.read())

    print(f"[SUCCESS] Audiobook created: {output_file}")

# ==========================
# MAIN
# ==========================

def main():
    print("[START] PDF → Audiobook (OpenAI TTS)")

    text = extract_text_from_pdf(PDF_PATH)

    if not text.strip():
        raise ValueError("No text extracted from PDF.")

    generate_audiobook(text, OUTPUT_AUDIO)

    print("[DONE] Audiobook generation complete.")

if __name__ == "__main__":
    main()
