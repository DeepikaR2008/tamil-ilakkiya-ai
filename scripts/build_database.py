"""
build_database.py
-----------------
Builds the ChromaDB vector database for Tamil Ilakkiya AI.

Steps:
1. Verifies processed data against validate_data.py (or allows dev-mode skip if testing).
2. Initializes persistent ChromaDB storage in database/chroma_db.
3. Loads all 7 literature datasets (Thirukkural, Purananuru, Akananuru, Natrinai, Kuruntokai, Silappathikaram, Manimekalai).
4. Generates multilingual embeddings and writes records in batches.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import chromadb
from scripts.validate_data import run_validation
from scripts.create_embeddings import MultilingualEmbeddingService

PROCESSED_DATA_DIR = ROOT_DIR / "data" / "processed"
CHROMA_DB_DIR = ROOT_DIR / "database" / "chroma_db"
COLLECTION_NAME = "tamil_ilakkiya_corpus"
BATCH_SIZE = 100

def sanitize_metadata(meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    ChromaDB metadata values must be int, float, str, or bool (cannot be None or complex dicts).
    """
    cleaned = {}
    for k, v in meta.items():
        if v is None:
            cleaned[k] = ""
        elif isinstance(v, (str, int, float, bool)):
            cleaned[k] = v
        else:
            cleaned[k] = str(v)
    return cleaned

def build_chroma_database(force_rebuild: bool = True, strict_validate: bool = True):
    print("=" * 60)
    print("Building ChromaDB Vector Knowledge Base — Tamil Ilakkiya AI")
    print("=" * 60)

    # 1. Validate corpus
    print("[1/4] Running corpus validation...")
    is_valid = run_validation(PROCESSED_DATA_DIR)
    if not is_valid and strict_validate:
        print("\n[!] Strict corpus validation FAILED or some files were missing.")
        print("    Database build aborted to preserve data integrity.")
        print("    (To build with available sample data for testing, use flag: --allow-partial)")
        return False

    # 2. Initialize ChromaDB client
    print(f"\n[2/4] Connecting to ChromaDB storage at: {CHROMA_DB_DIR}...")
    CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))

    if force_rebuild:
        existing_cols = [c.name for c in client.list_collections()]
        if COLLECTION_NAME in existing_cols:
            print(f"[*] Removing existing collection '{COLLECTION_NAME}' for fresh build...")
            client.delete_collection(COLLECTION_NAME)

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine", "description": "Tamil Classical Literature Knowledge Base"}
    )

    # 3. Load Multilingual Embedding Model
    print("\n[3/4] Initializing Multilingual Embedding Service...")
    embedder = MultilingualEmbeddingService()

    # 4. Ingest all files
    json_files = sorted(list(PROCESSED_DATA_DIR.glob("*.json")))
    if not json_files:
        print(f"[!] No processed JSON files found in {PROCESSED_DATA_DIR}.")
        return False

    print(f"\n[4/4] Ingesting {len(json_files)} literature files into ChromaDB...")
    total_indexed = 0

    for fpath in json_files:
        print(f"\n-> Loading {fpath.name}...")
        with open(fpath, "r", encoding="utf-8") as f:
            records = json.load(f)

        docs = []
        metas = []
        ids = []

        for item in records:
            doc_id = item.get("id")
            doc_text = item.get("text", "").strip()
            raw_meta = item.get("metadata", {})

            if not doc_id or not doc_text:
                continue

            clean_meta = sanitize_metadata(raw_meta)
            docs.append(doc_text)
            metas.append(clean_meta)
            ids.append(str(doc_id))

        if not docs:
            continue

        print(f"   Generating embeddings and adding {len(docs)} documents in batches of {BATCH_SIZE}...")
        for i in range(0, len(docs), BATCH_SIZE):
            batch_docs = docs[i : i + BATCH_SIZE]
            batch_metas = metas[i : i + BATCH_SIZE]
            batch_ids = ids[i : i + BATCH_SIZE]

            # Generate dense embeddings
            batch_embeddings = embedder.encode_documents(batch_docs, batch_size=len(batch_docs))

            collection.add(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_metas,
                embeddings=batch_embeddings
            )
            total_indexed += len(batch_docs)
            print(f"   ... Indexed {min(i + BATCH_SIZE, len(docs))}/{len(docs)} records", end="\r")

        print(f"\n   [OK] Finished indexing {fpath.name} ({len(docs)} items).")

    print("\n" + "=" * 60)
    print(f"[SUCCESS] ChromaDB build complete! Total documents indexed: {total_indexed}")
    print(f"Collection: '{COLLECTION_NAME}' | Location: {CHROMA_DB_DIR}")
    print("=" * 60)
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build ChromaDB for Tamil Ilakkiya AI")
    parser.add_argument("--allow-partial", action="store_true", help="Allow partial/sample data build without strict count enforcement")
    parser.add_argument("--no-rebuild", action="store_true", help="Do not wipe existing collection")
    args = parser.parse_args()

    build_chroma_database(
        force_rebuild=not args.no_rebuild,
        strict_validate=not args.allow_partial
    )
