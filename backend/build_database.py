import json
import os
import glob
import chromadb
from sentence_transformers import SentenceTransformer


# ============================================================
# Tamil Ilakkiya AI - Full Literature Database Builder
# ============================================================

print("\n==============================================")
print(" Tamil Ilakkiya AI - Database Builder")
print("==============================================\n")


# ------------------------------------------------------------
# 1. Load embedding model
# ------------------------------------------------------------

print("Loading embedding model...")

model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

print("Embedding model loaded.\n")


# ------------------------------------------------------------
# 2. Literature files
# ------------------------------------------------------------

sentamizh_dir = os.path.join(
    "sentamizh",
    "data",
    "processed"
)


literature_files = {
    "Purananuru": os.path.join(
        sentamizh_dir,
        "Purananuru_All.json"
    ),

    "Akananuru": os.path.join(
        sentamizh_dir,
        "Akananuru_All.json"
    ),

    "Kuruntokai": os.path.join(
        sentamizh_dir,
        "Kuruntokai_Vaidehi_All.json"
    ),

    "Natrinai": os.path.join(
        sentamizh_dir,
        "Natrinai_Vaidehi_All.json"
    ),

    "Silappatikaram": os.path.join(
        sentamizh_dir,
        "Silappatikaram_All.json"
    ),

    "Manimekalai": os.path.join(
        sentamizh_dir,
        "Manimekalai_All.json"
    ),

    "Thirukkural": "thirukkural_full.json"
}


# ------------------------------------------------------------
# 3. Read JSON safely
# ------------------------------------------------------------

def load_json(path):

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ------------------------------------------------------------
# 4. Convert any JSON structure to records
# ------------------------------------------------------------

def extract_records(data):

    if isinstance(data, list):
        return data

    if isinstance(data, dict):

        # Thirukkural structure
        if "kural" in data:
            return data["kural"]

        # Try common container names
        for key in [
            "data",
            "records",
            "verses",
            "entries",
            "poems"
        ]:

            if key in data and isinstance(
                data[key],
                list
            ):
                return data[key]

        # If dictionary itself represents one record
        return [data]

    return []


# ------------------------------------------------------------
# 5. Get text from a record
# ------------------------------------------------------------

def get_text(record):

    possible_fields = [

        "text_tamil",
        "classical_tamil",
        "tamil",
        "text",
        "Text",
        "verse",
        "Verse",
        "source_text",
        "modern_tamil",
        "Line1",
        "Line2",
        "couplet"
    ]

    pieces = []

    for field in possible_fields:

        value = record.get(field)

        if isinstance(value, str) and value.strip():

            pieces.append(value.strip())

    # Remove duplicates while preserving order

    unique = []

    for item in pieces:

        if item not in unique:
            unique.append(item)

    return " ".join(unique)


# ------------------------------------------------------------
# 6. Get number
# ------------------------------------------------------------

def get_number(record, index):

    possible_fields = [

        "verse_number",
        "Number",
        "number",
        "poem_number",
        "id",
        "ID"
    ]

    for field in possible_fields:

        value = record.get(field)

        if value is not None:

            return str(value)

    return str(index + 1)


# ------------------------------------------------------------
# 7. Get English meaning
# ------------------------------------------------------------

def get_english(record):

    possible_fields = [

        "meaning_english",
        "Translation",
        "translation",
        "english",
        "English",
        "Meaning",
        "meaning"
    ]

    for field in possible_fields:

        value = record.get(field)

        if isinstance(value, str) and value.strip():

            return value.strip()

    return ""


# ------------------------------------------------------------
# 8. Normalize one literature record
# ------------------------------------------------------------

def normalize_record(
    work,
    record,
    index
):

    tamil_text = get_text(record)

    english = get_english(record)

    number = get_number(
        record,
        index
    )

    if not tamil_text:

        return None

    record_id = (
        work.lower()
        .replace(" ", "_")
        + "_"
        + str(number)
        + "_"
        + str(index)
    )

    searchable_text = tamil_text

    if english:

        searchable_text += (
            " "
            + english
        )

    return {

        "id": record_id,

        "work": work,

        "verse_number": number,

        "text_tamil": tamil_text,

        "meaning_english": english,

        "searchable_text": searchable_text,

        "source_type": "classical_tamil_literature"
    }


# ------------------------------------------------------------
# 9. Load all literature
# ------------------------------------------------------------

all_records = []


for work, path in literature_files.items():

    print(
        f"Loading {work}..."
    )

    if not os.path.exists(path):

        print(
            f"WARNING: File not found: {path}"
        )

        continue

    data = load_json(path)

    records = extract_records(data)

    print(
        f"  Records found: {len(records)}"
    )

    for index, record in enumerate(records):

        if not isinstance(record, dict):
            continue

        normalized = normalize_record(
            work,
            record,
            index
        )

        if normalized:

            all_records.append(
                normalized
            )


# ------------------------------------------------------------
# 10. Show totals
# ------------------------------------------------------------

print("\n==============================================")
print(" Literature totals")
print("==============================================\n")


work_counts = {}


for record in all_records:

    work = record["work"]

    work_counts[work] = (
        work_counts.get(work, 0) + 1
    )


for work, count in work_counts.items():

    print(
        f"{work}: {count}"
    )


print(
    f"\nTOTAL RECORDS: {len(all_records)}"
)


# ------------------------------------------------------------
# 11. Create ChromaDB
# ------------------------------------------------------------

print("\nCreating ChromaDB...")


client = chromadb.PersistentClient(
    path="./chroma_db"
)


# Delete old collection if it exists

try:

    client.delete_collection(
        "tamil_literature"
    )

    print(
        "Old literature collection deleted."
    )

except Exception:

    pass


collection = client.create_collection(
    name="tamil_literature"
)


# ------------------------------------------------------------
# 12. Add records in batches
# ------------------------------------------------------------

BATCH_SIZE = 100


for start in range(
    0,
    len(all_records),
    BATCH_SIZE
):

    batch = all_records[
        start:start + BATCH_SIZE
    ]

    texts = [
        item["searchable_text"]
        for item in batch
    ]

    ids = [
        item["id"]
        for item in batch
    ]

    metadatas = []

    for item in batch:

        metadatas.append({

            "work": item["work"],

            "verse_number": item[
                "verse_number"
            ],

            "text_tamil": item[
                "text_tamil"
            ],

            "meaning_english": item[
                "meaning_english"
            ],

            "source_type": item[
                "source_type"
            ]
        })


    print(
        f"Embedding records "
        f"{start + 1} - "
        f"{min(start + BATCH_SIZE, len(all_records))} "
        f"of {len(all_records)}..."
    )


    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False
    ).tolist()


    collection.add(

        ids=ids,

        documents=texts,

        embeddings=embeddings,

        metadatas=metadatas
    )


# ------------------------------------------------------------
# 13. Final verification
# ------------------------------------------------------------

print("\n==============================================")
print(" DATABASE BUILD COMPLETE")
print("==============================================\n")


print(
    "ChromaDB records:",
    collection.count()
)


print("\nLiterature summary:")

for work, count in work_counts.items():

    print(
        f"  {work}: {count}"
    )


print(
    "\nDatabase location: ./chroma_db"
)

print(
    "\nTamil Ilakkiya AI database is ready."
)