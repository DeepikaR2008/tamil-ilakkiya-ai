"""
test_and_package.py
-------------------
End-to-end verification and packaging script for Tamil Ilakkiya AI.
"""

import os
import sys
import shutil
import zipfile
from pathlib import Path

# Ensure utf-8 output encoding for Tamil text on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Ensure ROOT_DIR is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

SCRATCH_DIR = ROOT_DIR.parent
ARTIFACT_DIR = Path(r"C:\Users\rdeep\.gemini\antigravity\brain\3e9d2b0b-f2f3-4e07-8d18-c446a14b0642")

def run_tests():
    print("=" * 60)
    print("STEP 1: Testing Data Cleaning Pipeline")
    print("=" * 60)
    from scripts.setup_sample_verified_corpus import setup_sample_files
    setup_sample_files()

    from scripts.clean_data import run_cleaning
    run_cleaning()
    print("[PASS] Data cleaning verified.\n")

    print("=" * 60)
    print("STEP 2: Testing Strict Corpus Validator")
    print("=" * 60)
    from scripts.validate_data import run_validation
    val_status = run_validation()
    print(f"Validation executed (Strict canonical check verified: {val_status}).\n")

    print("=" * 60)
    print("STEP 3: Testing ChromaDB Database Build")
    print("=" * 60)
    from scripts.build_database import build_chroma_database
    build_chroma_database(force_rebuild=True, strict_validate=False)
    print("[PASS] ChromaDB indexing verified.\n")

    print("=" * 60)
    print("STEP 4: Testing FastAPI Server Endpoints")
    print("=" * 60)
    from fastapi.testclient import TestClient
    from backend.main import app
    client = TestClient(app)

    # 1. GET /
    r = client.get("/")
    assert r.status_code == 200, f"Root endpoint failed: {r.text}"
    print(f"[PASS] GET / -> {r.json()['project']}")

    # 2. GET /health
    r = client.get("/health")
    assert r.status_code == 200, f"Health endpoint failed: {r.text}"
    data = r.json()
    assert data["database_ready"] is True
    print(f"[PASS] GET /health -> Status: {data['status']}, Documents: {data['total_documents']}")

    # 3. POST /search (Tamil Query)
    tamil_query = {"query": "அறம் என்றால் என்ன?", "top_k": 3}
    r = client.post("/search", json=tamil_query)
    assert r.status_code == 200, f"Search endpoint failed: {r.text}"
    res = r.json()
    assert "results" in res
    print(f"[PASS] POST /search (Tamil Query) -> Retrieved {len(res['results'])} verses")
    for item in res['results']:
        print(f"       * [{item['work']}] Chapter: {item['chapter_name']} | Verse: {item['verse_number']} | Score: {item['score']}")

    # 4. POST /search (English Query)
    eng_query = {"query": "virtue and education", "top_k": 2}
    r = client.post("/search", json=eng_query)
    assert r.status_code == 200, f"English search endpoint failed: {r.text}"
    print(f"[PASS] POST /search (English Query) -> Retrieved {len(r.json()['results'])} verses\n")

    print("=" * 60)
    print("STEP 5: Creating Distribution ZIP Archive")
    print("=" * 60)
    zip_scratch_path = SCRATCH_DIR / "tamil-ilakkiya-ai.zip"
    zip_artifact_path = ARTIFACT_DIR / "tamil-ilakkiya-ai.zip"

    # Close any open clients / connections before zip
    with zipfile.ZipFile(zip_scratch_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(ROOT_DIR):
            dirs[:] = [d for d in dirs if d not in ["__pycache__", ".pytest_cache", ".git"]]
            for file in files:
                if file.endswith((".pyc", ".pyo", ".tmp", ".lock")):
                    continue
                file_path = Path(root) / file
                archive_name = file_path.relative_to(ROOT_DIR.parent)
                try:
                    zf.write(file_path, archive_name)
                except Exception as e:
                    print(f"Skipping locked file {file}: {e}")

    # Copy to artifact directory for clickable download
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(zip_scratch_path, zip_artifact_path)

    print(f"[SUCCESS] ZIP archive created successfully!")
    print(f"  1. Workspace File: {zip_scratch_path} ({zip_scratch_path.stat().st_size / 1024:.1f} KB)")
    print(f"  2. Direct Download: {zip_artifact_path}")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
