import os
import json
from pathlib import Path
from typing import Dict, Any, List

from helpers import chunk_transcript_by_tokens  # Make sure import is correct

# Change this to your actual file name
TRANSCRIPT_FILENAME = "2025-07-01 - TKRG Planning.txt"
TRANSCRIPT_DIR = Path(__file__).resolve().parent / "transcripts"
INPUT_FILE_PATH = TRANSCRIPT_DIR / TRANSCRIPT_FILENAME
OUTPUT_FILE_PATH = TRANSCRIPT_DIR / f"{TRANSCRIPT_FILENAME.replace('.txt', '')}_chunks.txt"

def load_raw_transcript(path: Path) -> Dict[str, Any]:
    """Reads raw transcript text and creates mock sentence structure."""
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    sentences = []
    for idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        sentences.append({
            "speaker_name": "Speaker",  # Dummy speaker
            "text": line,
            "start_time": idx * 5,  # 5 sec apart (mock timing)
            "end_time": (idx + 1) * 5,
        })

    return {"sentences": sentences}

def save_chunks_to_file(chunks: List[Dict[str, Any]], path: Path):
    with open(path, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(f"\n--- Chunk {chunk['chunk_id']} ---\n")
            f.write(f"Token count: {chunk['token_count']}\n")
            f.write(f"Speakers: {', '.join(chunk['speakers'])}\n")
            f.write(f"Time Range: {chunk['time_range']}\n")
            f.write(f"Sentence Count: {chunk['sentence_count']}\n")
            f.write("Content:\n")
            f.write(chunk["content"])
            f.write("\n\n")

def main():
    if not INPUT_FILE_PATH.exists():
        print(f"Input file not found: {INPUT_FILE_PATH}")
        return

    print(f"Reading transcript from: {INPUT_FILE_PATH}")
    transcript_data = load_raw_transcript(INPUT_FILE_PATH)

    print("Chunking transcript...")
    chunks = chunk_transcript_by_tokens(transcript_data)

    print(f"Saving {len(chunks)} chunks to file: {OUTPUT_FILE_PATH}")
    save_chunks_to_file(chunks, OUTPUT_FILE_PATH)
    print("Done!")

if __name__ == "__main__":
    main()
