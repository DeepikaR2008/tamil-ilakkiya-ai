"""
clean_data.py
-------------
Data cleaning pipeline for Tamil Ilakkiya AI.

Responsibilities:
1. Strips HTML/XML tags if present.
2. Normalizes non-essential whitespace while preserving verse structure.
3. Preserves Tamil Unicode (using unicodedata.normalize 'NFC').
4. Retains meaningful punctuation and exact verse text.
5. Flags empty records and duplicates.
6. Formats clean JSON records to data/processed/.
"""

import os
import re
import json
import unicodedata
from pathlib import Path
from typing import List, Dict, Any, Tuple

RAW_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
PROCESSED_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"

HTML_TAG_REGEX = re.compile(r"<[^>]+>")
WHITESPACE_REGEX = re.compile(r"[ \t]+")
MULTIPLE_NEWLINES_REGEX = re.compile(r"\n\s*\n+")

def clean_tamil_text(raw_text: str) -> str:
    """
    Cleans raw Tamil text strictly preserving literary content and Unicode integrity.
    """
    if not raw_text or not isinstance(raw_text, str):
        return ""

    # 1. Normalize Unicode to Canonical Decomposition / Composition (NFC)
    text = unicodedata.normalize("NFC", raw_text)

    # 2. Remove HTML / XML tags
    text = HTML_TAG_REGEX.sub("", text)

    # 3. Normalize horizontal whitespace per line
    lines = text.strip().splitlines()
    cleaned_lines = []
    for line in lines:
        cleaned_line = WHITESPACE_REGEX.sub(" ", line).strip()
        if cleaned_line:
            cleaned_lines.append(cleaned_line)

    text = "\n".join(cleaned_lines)
    return text

def clean_record(record: Dict[str, Any], work_name: str) -> Tuple[Dict[str, Any] or None, str or None]:
    """
    Cleans and standardizes a single literature record.
    Returns (cleaned_record, error_message).
    """
    raw_text = record.get("text", "")
    text = clean_tamil_text(raw_text)

    if not text:
        return None, f"Empty text encountered in record ID: {record.get('id', 'unknown')}"

    metadata = record.get("metadata", {})
    if not isinstance(metadata, dict):
        return None, f"Invalid metadata structure in record ID: {record.get('id', 'unknown')}"

    # Verify work name consistency
    record_work = metadata.get("work", work_name)
    metadata["work"] = record_work

    cleaned_obj = {
        "id": str(record.get("id", "")).strip(),
        "text": text,
        "metadata": metadata
    }
    return cleaned_obj, None

def process_file(file_path: Path) -> Dict[str, Any]:
    """
    Cleans a JSON file of raw literature records and produces a cleaned version.
    """
    work_name = file_path.stem
    print(f"[*] Processing: {file_path.name} (Work: {work_name})...")

    with open(file_path, "r", encoding="utf-8") as f:
        try:
            raw_data = json.load(f)
        except Exception as e:
            return {"status": "error", "file": file_path.name, "error": f"JSON decode failed: {str(e)}"}

    if not isinstance(raw_data, list):
        return {"status": "error", "file": file_path.name, "error": "Root JSON element must be an array of records"}

    cleaned_records = []
    seen_ids = set()
    seen_verse_numbers = set()
    errors = []
    duplicate_count = 0

    for idx, item in enumerate(raw_data):
        rec_id = item.get("id")
        if rec_id in seen_ids:
            duplicate_count += 1
            errors.append(f"Duplicate record ID found: {rec_id} at item {idx}")
            continue

        cleaned_item, err = clean_record(item, work_name)
        if err:
            errors.append(err)
            continue

        # Check duplicate verse/poem within same work
        verse_key = None
        m = cleaned_item["metadata"]
        if "verse_number" in m and m["verse_number"] is not None:
            verse_key = ("verse", m["verse_number"], m.get("chapter_number"))
        elif "poem_number" in m and m["poem_number"] is not None:
            verse_key = ("poem", m["poem_number"])

        if verse_key:
            if verse_key in seen_verse_numbers:
                errors.append(f"Duplicate verse/poem identifier: {verse_key}")
            else:
                seen_verse_numbers.add(verse_key)

        seen_ids.add(rec_id)
        cleaned_records.append(cleaned_item)

    # Save cleaned file
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DATA_DIR / f"{work_name}.json"
    with open(out_path, "w", encoding="utf-8") as out_f:
        json.dump(cleaned_records, out_f, ensure_ascii=False, indent=2)

    return {
        "status": "success",
        "file": file_path.name,
        "input_count": len(raw_data),
        "output_count": len(cleaned_records),
        "duplicates_skipped": duplicate_count,
        "errors": errors
    }

def run_cleaning():
    print("=" * 60)
    print("Tamil Ilakkiya AI — Data Cleaning Pipeline")
    print("=" * 60)
    
    if not RAW_DATA_DIR.exists():
        print(f"[!] Raw data directory not found at: {RAW_DATA_DIR}")
        print("    Please create raw data files in data/raw/ before running cleaning.")
        return

    raw_files = list(RAW_DATA_DIR.glob("*.json"))
    if not raw_files:
        print(f"[!] No .json files found in {RAW_DATA_DIR}")
        return

    summary_reports = []
    for f in raw_files:
        report = process_file(f)
        summary_reports.append(report)

    print("\n--- Cleaning Summary ---")
    for r in summary_reports:
        if r["status"] == "success":
            print(f"-> {r['file']}: Input={r['input_count']} | Cleaned={r['output_count']} | Duplicates={r['duplicates_skipped']} | Errors={len(r['errors'])}")
            if r["errors"]:
                for e in r["errors"][:5]:
                    print(f"   - Warn: {e}")
                if len(r["errors"]) > 5:
                    print(f"   ... and {len(r['errors'])-5} more warnings")
        else:
            print(f"-> [ERROR] {r['file']}: {r['error']}")
    print("=" * 60)

if __name__ == "__main__":
    run_cleaning()
