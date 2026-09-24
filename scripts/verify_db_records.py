import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('database/literature.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("--- Thirukkural Kural 1 ---")
cursor.execute("SELECT * FROM literature_corpus WHERE id = 'thirukkural_1';")
r1 = dict(cursor.fetchone())
print("Tamil text:\n", r1['text_tamil'])
print("English couplet:\n", r1['text_english'])
print("Hindi couplet:\n", r1['text_hindi'])
print("Title EN:", r1['title_english'], "| Title HI:", r1['title_hindi'])

print("\n--- Thirukkural Kural 781 ---")
cursor.execute("SELECT * FROM literature_corpus WHERE id = 'thirukkural_781';")
r781 = dict(cursor.fetchone())
print("Tamil text:\n", r781['text_tamil'])
print("English couplet:\n", r781['text_english'])
print("Hindi couplet:\n", r781['text_hindi'])
print("Title EN:", r781['title_english'], "| Title HI:", r781['title_hindi'])

print("\n--- Kuruntokai Poem 1 ---")
cursor.execute("SELECT * FROM literature_corpus WHERE id = 'kuruntokai_1';")
rk1 = dict(cursor.fetchone())
print("Tamil text:\n", rk1['text_tamil'][:60])
print("English poem:\n", rk1['text_english'][:120])
print("Hindi poem:\n", rk1['text_hindi'][:120])

print("\n--- Purananuru Poem 192 ---")
cursor.execute("SELECT * FROM literature_corpus WHERE work = 'Purananuru' AND verse_number = 192;")
rp192 = dict(cursor.fetchone())
print("Tamil text:\n", rp192['text_tamil'][:60])
print("English poem:\n", rp192['text_english'][:120])
print("Hindi poem:\n", rp192['text_hindi'][:120])

conn.close()
