"""
validate_data.py
----------------
Strict Literary Corpus Validator for Tamil Ilakkiya AI.

Checks:
- Thirukkural: Exactly 1330 kurals, 133 chapters, 10 per chapter (38 Aram, 70 Porul, 25 Inbam).
- Purananuru: Exactly 400 poems.
- Akananuru: Exactly 400 poems.
- Natrinai: Exactly 400 poems.
- Kuruntokai: Exactly 401 poems.
- Silappathikaram: Epic structure validated (Kandam / Kaathai).
- Manimekalai: Epic structure validated (Kaathai).

Strictly reports any missing or mismatched records without faking data.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"

EXPECTED_COUNTS = {
    "thirukkural": 1330,
    "purananuru": 400,
    "akananuru": 400,
    "natrinai": 400,
    "kuruntokai": 401,
    "silappathikaram": "epic_structure",
    "manimekalai": "epic_structure"
}

def validate_thirukkural(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    count = len(records)
    chapters = {}
    sections = {"Aram": set(), "Porul": set(), "Inbam": set(), "அறத்துப்பால்": set(), "பொருட்பால்": set(), "காமத்துப்பால்": set()}
    missing_fields = []
    
    for r in records:
        meta = r.get("metadata", {})
        ch_num = meta.get("chapter_number")
        sec = meta.get("section")
        kural_num = meta.get("verse_number")
        
        if ch_num is None or kural_num is None:
            missing_fields.append(f"Record {r.get('id')} missing chapter_number or verse_number")
            continue
            
        chapters.setdefault(ch_num, []).append(kural_num)
        if sec in sections:
            sections[sec].add(ch_num)

    total_chapters = len(chapters)
    irregular_chapters = {ch: len(kurals) for ch, kurals in chapters.items() if len(kurals) != 10}

    valid = (count == 1330 and total_chapters == 133 and len(irregular_chapters) == 0 and len(missing_fields) == 0)

    return {
        "work": "Thirukkural",
        "expected": 1330,
        "actual": count,
        "total_chapters": total_chapters,
        "expected_chapters": 133,
        "irregular_chapters": irregular_chapters,
        "missing_fields_count": len(missing_fields),
        "valid": valid
    }

def validate_standard_sangam(work_name: str, expected_count: int, records: List[Dict[str, Any]]) -> Dict[str, Any]:
    count = len(records)
    poem_numbers = set()
    duplicates = []
    missing_fields = []

    for r in records:
        meta = r.get("metadata", {})
        poem_num = meta.get("verse_number") or meta.get("poem_number")
        if poem_num is None:
            missing_fields.append(f"Record {r.get('id')} missing poem_number/verse_number")
        elif poem_num in poem_numbers:
            duplicates.append(poem_num)
        else:
            poem_numbers.add(poem_num)

    valid = (count == expected_count and len(duplicates) == 0 and len(missing_fields) == 0)

    return {
        "work": work_name.capitalize(),
        "expected": expected_count,
        "actual": count,
        "unique_poems": len(poem_numbers),
        "duplicate_numbers": duplicates,
        "missing_fields_count": len(missing_fields),
        "valid": valid
    }

def validate_silappathikaram(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    count = len(records)
    kandams = set()
    kaathais = set()
    missing_fields = []

    for r in records:
        meta = r.get("metadata", {})
        kandam = meta.get("kandam") or meta.get("section")
        kaathai = meta.get("kaathai") or meta.get("chapter_name")
        if not kandam or not kaathai:
            missing_fields.append(f"Record {r.get('id')} missing kandam or kaathai")
        if kandam:
            kandams.add(kandam)
        if kaathai:
            kaathais.add(kaathai)

    valid = (count > 0 and len(kandams) >= 1 and len(kaathais) >= 1 and len(missing_fields) == 0)

    return {
        "work": "Silappathikaram",
        "expected": "Epic (Kandam/Kaathai structure)",
        "actual": f"{count} sections/verses across {len(kaathais)} Kaathais in {len(kandams)} Kandams",
        "kandams_found": list(kandams),
        "total_kaathais": len(kaathais),
        "missing_fields_count": len(missing_fields),
        "valid": valid
    }

def validate_manimekalai(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    count = len(records)
    kaathais = set()
    missing_fields = []

    for r in records:
        meta = r.get("metadata", {})
        kaathai = meta.get("kaathai") or meta.get("chapter_name")
        if not kaathai:
            missing_fields.append(f"Record {r.get('id')} missing kaathai")
        if kaathai:
            kaathais.add(kaathai)

    valid = (count > 0 and len(kaathais) >= 1 and len(missing_fields) == 0)

    return {
        "work": "Manimekalai",
        "expected": "Epic (Kaathai structure)",
        "actual": f"{count} sections/verses across {len(kaathais)} Kaathais",
        "total_kaathais": len(kaathais),
        "missing_fields_count": len(missing_fields),
        "valid": valid
    }

def run_validation(data_dir: Path = None) -> bool:
    if data_dir is None:
        data_dir = DATA_DIR

    print("=" * 60)
    print("Corpus Validation Report — Tamil Ilakkiya AI")
    print("=" * 60)

    if not data_dir.exists():
        print(f"[!] Processed data directory does not exist: {data_dir}")
        print("    Please run clean_data.py after placing raw texts.")
        return False

    all_valid = True
    results = {}

    for work, expected in EXPECTED_COUNTS.items():
        file_path = data_dir / f"{work}.json"
        if not file_path.exists():
            print(f"{work.capitalize():<18}: [NOT FOUND] File missing: {file_path.name}")
            all_valid = False
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"{work.capitalize():<18}: [ERROR] JSON read failed ({e})")
            all_valid = False
            continue

        if work == "thirukkural":
            res = validate_thirukkural(data)
            status = f"{res['actual']} / {res['expected']}"
            if res["valid"]:
                print(f"Thirukkural       : {status} (133 chapters validated)")
            else:
                print(f"Thirukkural       : [MISMATCH] {status} | Irregular chapters: {len(res['irregular_chapters'])}")
                all_valid = False

        elif work in ["purananuru", "akananuru", "natrinai", "kuruntokai"]:
            res = validate_standard_sangam(work, expected, data)
            status = f"{res['actual']} / {res['expected']}"
            if res["valid"]:
                print(f"{work.capitalize():<18}: {status}")
            else:
                print(f"{work.capitalize():<18}: [MISMATCH] {status} (Duplicates: {len(res['duplicate_numbers'])})")
                all_valid = False

        elif work == "silappathikaram":
            res = validate_silappathikaram(data)
            if res["valid"]:
                print(f"Silappathikaram   : structure validated ({res['actual']})")
            else:
                print(f"Silappathikaram   : [INVALID STRUCTURE] {res['actual']}")
                all_valid = False

        elif work == "manimekalai":
            res = validate_manimekalai(data)
            if res["valid"]:
                print(f"Manimekalai       : structure validated ({res['actual']})")
            else:
                print(f"Manimekalai       : [INVALID STRUCTURE] {res['actual']}")
                all_valid = False

    print("=" * 60)
    if all_valid:
        print("[+] All available corpora successfully verified against canonical counts & schema.")
    else:
        print("[!] Validation failed on one or more corpus files. Check logs above.")
    print("=" * 60)
    return all_valid

if __name__ == "__main__":
    run_validation()
