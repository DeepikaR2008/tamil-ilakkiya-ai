import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('database/literature.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('PRAGMA table_info(literature_corpus);')
cols = [r['name'] for r in cursor.fetchall()]
print('Columns:', cols)

cursor.execute('SELECT work, COUNT(*) FROM literature_corpus GROUP BY work;')
for r in cursor.fetchall():
    print(r[0], ':', r[1])

print('\n--- Thirukkural Sample ---')
cursor.execute("SELECT * FROM literature_corpus WHERE work = 'Thirukkural' LIMIT 1;")
sample = dict(cursor.fetchone())
for k, v in sample.items():
    if v and len(str(v)) > 80:
        print(f'{k}: {str(v)[:80]}...')
    else:
        print(f'{k}: {v}')

print('\n--- Purananuru Sample ---')
cursor.execute("SELECT * FROM literature_corpus WHERE work = 'Purananuru' LIMIT 1;")
sample2 = dict(cursor.fetchone())
for k, v in sample2.items():
    if v and len(str(v)) > 80:
        print(f'{k}: {str(v)[:80]}...')
    else:
        print(f'{k}: {v}')
