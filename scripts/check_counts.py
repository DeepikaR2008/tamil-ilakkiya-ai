import sqlite3
import json
from pathlib import Path

# Connect to database
db_path = Path("database/literature.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check works
cursor.execute("SELECT work, COUNT(*) FROM literature_corpus GROUP BY work;")
works_count = {r[0]: r[1] for r in cursor.fetchall()}
print("Corpus by work:", works_count)

conn.close()
