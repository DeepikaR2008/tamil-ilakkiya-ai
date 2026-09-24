import sqlite3
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('database/literature.db')
c = conn.cursor()
c.execute("""
    SELECT chapter_number, chapter_name, section 
    FROM literature_corpus 
    WHERE work = 'Thirukkural' 
    GROUP BY chapter_number 
    ORDER BY chapter_number ASC;
""")
rows = c.fetchall()
conn.close()

with open('scripts/thirukkural_chapters.json', 'w', encoding='utf-8') as f:
    json.dump([{'num': r[0], 'name': r[1], 'section': r[2]} for r in rows], f, ensure_ascii=False, indent=2)

print(f"Exported {len(rows)} chapters successfully.")
