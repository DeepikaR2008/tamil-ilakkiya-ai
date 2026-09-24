"""
build_full_database.py
----------------------
Compiles the complete 7 canonical works of Tamil classical literature into
a clean, persistent SQLite database and pre-computes fast retrieval indexes.

Works included:
1. Thirukkural: 1,330 Kurals (133 Chapters / Adhikarams, 3 Paals)
2. Purananuru: 388/400 Poems (authentic classical Sangam anthology)
3. Akananuru: 400 Poems (complete Sangam akam anthology)
4. Natrinai: 396/400 Poems (classical Sangam anthology)
5. Kuruntokai: 400 Poems (classical Sangam love lyric anthology)
6. Silappathikaram: Complete Pukar Kandam epic cantos
7. Manimekalai: Complete epic narrative sections
"""

import os
import sys
import re
import json
import sqlite3
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "database"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "literature.db"

# Source Data Locations
SENTAMIZH_DIR = Path(r"C:\Users\rdeep\OneDrive\Deepika\Tamil-Ilakkiya-AI\backend\sentamizh-corpus-main\data\processed")
TK_PATH = Path(r"C:\Users\rdeep\OneDrive\Deepika\Tamil-Ilakkiya-AI\backend\thirukkural_full.json")

# Fallback path if OneDrive not accessible
if not TK_PATH.exists():
    TK_PATH = Path(r"C:\Users\rdeep\Downloads\Tamil-Ilakkiya-AI\backend\literature_data\sentamizh-corpus-main\thirukkural_full.json")

# 133 Thirukkural Adhikarams with Paal
THIRUKKURAL_CHAPTERS = [
    # 1 - 38: Aram (அறத்துப்பால்)
    (1, "கடவுள் வாழ்த்து", "அறத்துப்பால்", "Aram / Virtue"),
    (2, "வான்சிறப்பு", "அறத்துப்பால்", "Aram / Virtue"),
    (3, "நீத்தார் பெருமை", "அறத்துப்பால்", "Aram / Virtue"),
    (4, "அறன் வலியுறுத்தல்", "அறத்துப்பால்", "Aram / Virtue"),
    (5, "இல்வாழ்க்கை", "அறத்துப்பால்", "Aram / Virtue"),
    (6, "வாழ்க்கைத்துணை நலம்", "அறத்துப்பால்", "Aram / Virtue"),
    (7, "புதல்வரைப் பெறுதல்", "அறத்துப்பால்", "Aram / Virtue"),
    (8, "அன்புடைமை", "அறத்துப்பால்", "Aram / Virtue"),
    (9, "விருந்தோம்பல்", "அறத்துப்பால்", "Aram / Virtue"),
    (10, "இனியவை கூறல்", "அறத்துப்பால்", "Aram / Virtue"),
    (11, "செய்ந்நன்றியறிதல்", "அறத்துப்பால்", "Aram / Virtue"),
    (12, "நடுவுநிலைமை", "அறத்துப்பால்", "Aram / Virtue"),
    (13, "அடக்கமுடைமை", "அறத்துப்பால்", "Aram / Virtue"),
    (14, "ஒழுக்கமுடைமை", "அறத்துப்பால்", "Aram / Virtue"),
    (15, "பிறனில் விழையாமை", "அறத்துப்பால்", "Aram / Virtue"),
    (16, "பொறையுடைமை", "அறத்துப்பால்", "Aram / Virtue"),
    (17, "அழுக்காறாமை", "அறத்துப்பால்", "Aram / Virtue"),
    (18, "வெஃகாமை", "அறத்துப்பால்", "Aram / Virtue"),
    (19, "புறங்கூறாமை", "அறத்துப்பால்", "Aram / Virtue"),
    (20, "பயனில சொல்லாமை", "அறத்துப்பால்", "Aram / Virtue"),
    (21, "தீவினையச்சம்", "அறத்துப்பால்", "Aram / Virtue"),
    (22, "ஒப்புரவறிதல்", "அறத்துப்பால்", "Aram / Virtue"),
    (23, "ஈகை", "அறத்துப்பால்", "Aram / Virtue"),
    (24, "புகழ்", "அறத்துப்பால்", "Aram / Virtue"),
    (25, "அருளுடைமை", "அறத்துப்பால்", "Aram / Virtue"),
    (26, "புலால் மறுத்தல்", "அறத்துப்பால்", "Aram / Virtue"),
    (27, "தவம்", "அறத்துப்பால்", "Aram / Virtue"),
    (28, "கூடாவொழுக்கம்", "அறத்துப்பால்", "Aram / Virtue"),
    (29, "கள்ளாமை", "அறத்துப்பால்", "Aram / Virtue"),
    (30, "வாய்மை", "அறத்துப்பால்", "Aram / Virtue"),
    (31, "வெகுளாமை", "அறத்துப்பால்", "Aram / Virtue"),
    (32, "இன்னாசெய்யாமை", "அறத்துப்பால்", "Aram / Virtue"),
    (33, "கொல்லாமை", "அறத்துப்பால்", "Aram / Virtue"),
    (34, "நிலையாமை", "அறத்துப்பால்", "Aram / Virtue"),
    (35, "துறவு", "அறத்துப்பால்", "Aram / Virtue"),
    (36, "மெய்யுணர்தல்", "அறத்துப்பால்", "Aram / Virtue"),
    (37, "அவாவறுத்தல்", "அறத்துப்பால்", "Aram / Virtue"),
    (38, "ஊழ்", "அறத்துப்பால்", "Aram / Virtue"),

    # 39 - 108: Porul (பொருட்பால்)
    (39, "இறைமாட்சி", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (40, "கல்வி", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (41, "கல்லாமை", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (42, "கேள்வி", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (43, "அறிவுடைமை", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (44, "குற்றங்கடிதல்", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (45, "பெரியாரைத் துணைக்கோடல்", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (46, "சிற்றினஞ்சேராமை", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (47, "தெரிந்துசெயல்வகை", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (48, "வலியறிதல்", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (49, "காலமறிதல்", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (50, "இடனறிதல்", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (51, "தெரிந்துதெளிதல்", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (52, "தெரிந்துவினையாடல்", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (53, "சுற்றந்தழால்", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (54, "பொள்ளாமை", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (55, "செங்கோன்மை", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (56, "கொடுங்கோன்மை", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (57, "வெருவந்தசெய்யாமை", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (58, "கண்ணோட்டம்", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (59, "ஒற்றாடல்", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (60, "ஊக்கமுடைமை", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (61, "மடியின்மை", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (62, "ஆள்வினையுடைமை", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (63, "இடுக்கணழியாமை", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (64, "அமைச்சு", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (65, "சொல்வன்மை", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (66, "வினைத்தூய்மை", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (67, "வினைத்திட்பம்", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (68, "வினைசெயல்வகை", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (69, "தூது", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (70, "மன்னரைச்சேர்ந்து ஒழுகுதல்", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (71, "குறிப்பறிதல்", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (72, "அவையறிதல்", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (73, "அவையஞ்சாமை", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (74, "நாடு", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (75, "அரண்", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (76, "பொருளசெயல்வகை", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (77, "படைமாட்சி", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (78, "படைச்செருக்கு", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (79, "நட்பு", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (80, "நட்பாராய்தல்", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (81, "பழைமை", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (82, "தீநட்பு", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (83, "கூடாநட்பு", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (84, "பேதைமை", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (85, "புல்லறிவாண்மை", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (86, "இகல்", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (87, "பகைமாட்சி", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (88, "பகைத்திறந்தெரிதல்", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (89, "உட்பகை", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (90, "பெரியாரைப் பிழையாமை", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (91, "பெண்வழிச்சேறல்", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (92, "வரைவின்மகளிர்", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (93, "கள்ளுண்ணாமை", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (94, "சூது", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (95, "மருந்து", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (96, "குடிமை", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (97, "மானம்", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (98, "பெருமை", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (99, "சான்றாண்மை", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (100, "பண்புடைமை", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (101, "நன்றியில்செல்வம்", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (102, "நாணுடைமை", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (103, "குடிசெயல்வகை", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (104, "உழவு", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (105, "நல்குரவு", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (106, "இரவு", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (107, "இரவச்சம்", "பொருட்பால்", "Porul / Wealth & Statecraft"),
    (108, "கயமை", "பொருட்பால்", "Porul / Wealth & Statecraft"),

    # 109 - 133: Inbam (காமத்துப்பால்)
    (109, "தகையணங்குறுத்தல்", "காமத்துப்பால்", "Inbam / Love"),
    (110, "குறிப்பறிதல்", "காமத்துப்பால்", "Inbam / Love"),
    (111, "புணர்ச்சிமகிழ்தல்", "காமத்துப்பால்", "Inbam / Love"),
    (112, "நலம்புனைந்துரைத்தல்", "காமத்துப்பால்", "Inbam / Love"),
    (113, "காதற்சிறப்புரைத்தல்", "காமத்துப்பால்", "Inbam / Love"),
    (114, "நாணுத்துறவுரைத்தல்", "காமத்துப்பால்", "Inbam / Love"),
    (115, "அலரறிவுறுத்தல்", "காமத்துப்பால்", "Inbam / Love"),
    (116, "பிரிவாற்றாமை", "காமத்துப்பால்", "Inbam / Love"),
    (117, "படர்மெலிந்திரங்கல்", "காமத்துப்பால்", "Inbam / Love"),
    (118, "கண்விதுப்பழிதல்", "காமத்துப்பால்", "Inbam / Love"),
    (119, "பசப்பறுபருவரல்", "காமத்துப்பால்", "Inbam / Love"),
    (120, "தனிப்படர்மிகுதி", "காமத்துப்பால்", "Inbam / Love"),
    (121, "நினைந்தவர்Message", "காமத்துப்பால்", "Inbam / Love"),
    (122, "கனவுநிலையுரைத்தல்", "காமத்துப்பால்", "Inbam / Love"),
    (123, "பொழுதுகண்டிரங்கல்", "காமத்துப்பால்", "Inbam / Love"),
    (124, "உறுப்புநலனழிதல்", "காமத்துப்பால்", "Inbam / Love"),
    (125, "நெஞ்சொடுகிளத்தல்", "காமத்துப்பால்", "Inbam / Love"),
    (126, "நிறையழிதல்", "காமத்துப்பால்", "Inbam / Love"),
    (127, "அவர்வயின்விதும்பல்", "காமத்துப்பால்", "Inbam / Love"),
    (128, "குறிப்பறிவுறுத்தல்", "காமத்துப்பால்", "Inbam / Love"),
    (129, "புணர்ச்சிவிதும்பல்", "காமத்துப்பால்", "Inbam / Love"),
    (130, "நெஞ்சொடுபுலத்தல்", "காமத்துப்பால்", "Inbam / Love"),
    (131, "புலவி", "காமத்துப்பால்", "Inbam / Love"),
    (132, "புலவிநுணுக்கம்", "காமத்துப்பால்", "Inbam / Love"),
    (133, "ஊடலுவகை", "காமத்துப்பால்", "Inbam / Love")
]

# Chapter lookup dictionary by chapter number
CHAPTER_MAP = {ch[0]: ch for ch in THIRUKKURAL_CHAPTERS}

def clean_pure_tamil(text: str) -> str:
    """Strips HTML tags, JSON fragments, debug codes, footnotes, and excess whitespace."""
    if not text:
        return ""
    # Strip broken unclosed tags like <br without closing > or #<br
    s = re.sub(r'#?<br\b[^>]*>?', '\n', str(text), flags=re.IGNORECASE)
    # Strip any regular HTML tags
    s = re.sub(r'<[^>]+>', ' ', s)
    # Strip leftover angle brackets
    s = re.sub(r'<|>', '', s)
    # Clean non-breaking spaces & zero-width characters
    s = s.replace('\xa0', ' ').replace('&nbsp;', ' ').replace('\u200c', '').replace('\u200d', '')
    # Clean debug prefixes or editorial notes like (சிந்தியல் வெண்பாக்கள்), (பா-வே.) ...
    s = re.sub(r'^\s*\(.*?\)\s*', '', s)
    # Clean footnote trailing lines like '----குடவாயிற்... (பா-வே.)...'
    s = re.sub(r'\n\s*----.*$', '', s, flags=re.DOTALL)
    # Remove leading commas or punctuation leftover from bad scrapers
    s = re.sub(r'^\s*[,;.-]\s*', '', s)
    # Remove isolated hash characters
    s = re.sub(r'#', '', s)
    # Normalize multiple blank lines to double newline
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s.strip()

def build_schema(conn: sqlite3.Connection):
    cursor = conn.cursor()
    
    # 1. Literature Corpus Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS literature_corpus (
        id TEXT PRIMARY KEY,
        work TEXT NOT NULL,
        group_name TEXT NOT NULL,
        section TEXT,
        chapter_number INTEGER,
        chapter_name TEXT,
        verse_number INTEGER,
        poet TEXT,
        text_tamil TEXT NOT NULL,
        text_transliteration TEXT,
        explanation_tamil TEXT,
        explanation_english TEXT,
        theme TEXT,
        search_tokens TEXT
    );
    """)

    # Indexes for lightning fast lookups
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_corpus_work ON literature_corpus(work);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_corpus_verse_num ON literature_corpus(work, verse_number);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_corpus_ch_num ON literature_corpus(work, chapter_number);")

    # 2. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. Sessions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # 4. History Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        citation TEXT,
        verse_id TEXT,
        work TEXT,
        confidence REAL,
        language TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # 5. Bookmarks Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookmarks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        verse_id TEXT NOT NULL,
        work TEXT NOT NULL,
        verse_number TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, verse_id),
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # 6. Exercises / Quizzes Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quizzes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        work TEXT NOT NULL,
        kural_number INTEGER,
        chapter_name TEXT,
        question_tamil TEXT NOT NULL,
        question_english TEXT,
        options_json TEXT NOT NULL,
        correct_index INTEGER NOT NULL,
        explanation_tamil TEXT NOT NULL
    );
    """)

    conn.commit()

def ingest_thirukkural(conn: sqlite3.Connection):
    cursor = conn.cursor()
    if not TK_PATH.exists():
        print(f"[!] Thirukkural file not found at {TK_PATH}")
        return 0

    print(f"[*] Ingesting Thirukkural from {TK_PATH}...")
    with open(TK_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    kurals = data.get('kural', [])
    records = []
    
    for item in kurals:
        num = int(item['Number'])
        ch_num = (num - 1) // 10 + 1
        ch_meta = CHAPTER_MAP.get(ch_num, (ch_num, f"அதிகாரம் {ch_num}", "அறத்துப்பால்", "Aram"))
        ch_name = ch_meta[1]
        section = ch_meta[2]
        
        line1 = item.get('Line1', '').strip()
        line2 = item.get('Line2', '').strip()
        text_tamil = clean_pure_tamil(f"{line1}\n{line2}")
        
        trans1 = item.get('transliteration1', '').strip()
        trans2 = item.get('transliteration2', '').strip()
        translit = f"{trans1} {trans2}".strip()
        
        # Best available Tamil explanation (Mu. Varadarajan preferred, or Solomon Pappaiah)
        mv = item.get('mv', '').strip()
        sp = item.get('sp', '').strip()
        mk = item.get('mk', '').strip()
        exp_tamil = mv if mv else (sp if sp else mk)
        exp_tamil = clean_pure_tamil(exp_tamil)
        
        exp_en = clean_pure_tamil(item.get('Translation', ''))
        theme = f"{section} {ch_name}"

        # Build search tokens
        tokens = f"thirukkural kural {num} {ch_name} {section} {text_tamil} {exp_tamil} {exp_en} {translit}".lower()

        records.append((
            f"thirukkural_{num}",
            "Thirukkural",
            "Sangam Literature",
            section,
            ch_num,
            ch_name,
            num,
            "திருவள்ளுவர்",
            text_tamil,
            translit,
            exp_tamil,
            exp_en,
            theme,
            tokens
        ))

    cursor.executemany("""
    INSERT OR REPLACE INTO literature_corpus (
        id, work, group_name, section, chapter_number, chapter_name,
        verse_number, poet, text_tamil, text_transliteration,
        explanation_tamil, explanation_english, theme, search_tokens
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, records)
    conn.commit()
    print(f"[+] Loaded {len(records)} Kurals into database.")
    return len(records)

def ingest_sentamizh_work(conn: sqlite3.Connection, filename: str, work_name: str, group_name: str, default_poet: str):
    cursor = conn.cursor()
    filepath = SENTAMIZH_DIR / filename
    if not filepath.exists():
        print(f"[!] File not found: {filepath}")
        return 0

    print(f"[*] Ingesting {work_name} from {filename}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        items = json.load(f)

    records = []
    for item in items:
        v_id_raw = item.get('verse_id', '')
        v_num_raw = item.get('verse_number', '')
        try:
            # Try parsing integer verse number
            v_num = int(re.sub(r'\D', '', str(v_num_raw))) if re.search(r'\d', str(v_num_raw)) else 1
        except Exception:
            v_num = 1

        doc_id = f"{work_name.lower()}_{v_num_raw}".replace('.', '_').replace('-', '_')
        
        # Clean Tamil text
        text_tamil = clean_pure_tamil(item.get('classical_tamil', ''))
        if not text_tamil or len(text_tamil) < 10:
            continue

        exp_tamil = clean_pure_tamil(item.get('modern_tamil') or '')
        exp_en = clean_pure_tamil(item.get('english') or '')

        # Metadata parsing
        context = item.get('cultural_context') or ''
        thinai = item.get('thinai') or ''
        turai = item.get('turai') or ''
        poet = default_poet
        
        # Extract poet if mentioned in context
        poet_match = re.search(r'(?:Author|Poet|பாடியவர்):\s*([^;,\n]+)', context, re.IGNORECASE)
        if poet_match:
            poet = poet_match.group(1).strip()

        # Extract chapter / section if mentioned
        ch_name = thinai or turai
        ch_match = re.search(r'(?:Kaathai|Chapter|காதை|அத்தியாயம்):\s*([^;,\n]+)', context, re.IGNORECASE)
        if ch_match:
            ch_name = ch_match.group(1).strip()
        elif not ch_name and context:
            ch_name = context.split(';')[0].strip()

        section = item.get('layer', group_name)
        theme = f"{thinai} {turai} {item.get('themes') or ''}".strip()
        
        tokens = f"{work_name} {v_num_raw} {ch_name} {poet} {text_tamil} {exp_tamil} {exp_en} {theme} {context}".lower()

        records.append((
            doc_id,
            work_name,
            group_name,
            section,
            v_num,
            ch_name,
            v_num,
            poet,
            text_tamil,
            "",
            exp_tamil if exp_tamil else f"{work_name} பாடல் {v_num_raw}. திணை: {thinai or 'குறிப்பிடப்படவில்லை'}.",
            exp_en if exp_en else f"{work_name} verse #{v_num_raw}. Classical Tamil anthology poem.",
            theme,
            tokens
        ))

    cursor.executemany("""
    INSERT OR REPLACE INTO literature_corpus (
        id, work, group_name, section, chapter_number, chapter_name,
        verse_number, poet, text_tamil, text_transliteration,
        explanation_tamil, explanation_english, theme, search_tokens
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, records)
    conn.commit()
    print(f"[+] Loaded {len(records)} poems for {work_name}.")
    return len(records)

def seed_thirukkural_quizzes(conn: sqlite3.Connection):
    """Seeds curated Thirukkural exam prep quiz questions for students."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM quizzes;")
    
    quiz_data = [
        (
            "Thirukkural", 1, "கடவுள் வாழ்த்து",
            "எழுத்துக்களுக்கு அகரம் முதன்மை போல உலகிற்கு எது முதன்மை என்று வள்ளுவர் கூறுகிறார்?",
            "What is primary to the world, as the letter 'A' is to alphabets?",
            json.dumps(["ஆதிபகவன் (இறைவன்)", "மன்னன்", "சூரியன்", "வானம்"], ensure_ascii=False),
            0,
            "அகர முதல எழுத்தெல்லாம் ஆதி பகவன் முதற்றே உலகு. (குறள் 1)"
        ),
        (
            "Thirukkural", 2, "கடவுள் வாழ்த்து",
            "கற்றதனால் மனிதனுக்கு ஏற்படும் தலையாய பயன் எது?",
            "What is the ultimate purpose of learning according to Valluvar?",
            json.dumps(["செல்வம் ஈட்டுவது", "தூய அறிவுடைய இறைவனின் திருவடிகளைத் தொழுவது", "அனைவரையும் அடக்குவது", "புகழ் பெறுவது"], ensure_ascii=False),
            1,
            "கற்றதனால் ஆய பயன்கொல் வாலறிவன் நற்றாள் தொழாஅர் எனின். (குறள் 2)"
        ),
        (
            "Thirukkural", 11, "வான்சிறப்பு",
            "உலகில் மழை பெய்யவில்லை என்றால் உலகிற்கு என்ன நேரிடும்?",
            "What happens if rain fails according to Vaan Sirappu?",
            json.dumps(["வெப்பம் குறையும்", "பசி உலகை வருத்தும், உயிர்கள் வாழ இயலாது", "காடு வளரும்", "விலைவாசி குறையும்"], ensure_ascii=False),
            1,
            "துப்பார்க்குத் துப்பாய துப்பாக்கித் துப்பார்க்குத் துப்பாய தூஉம் மழை. (குறள் 12)"
        ),
        (
            "Thirukkural", 71, "அன்புடைமை",
            "அன்பில்லாதவர்கள் எதனைத் தமக்குரியதாகக் கருதுவர்?",
            "What do people without love consider exclusively their own?",
            json.dumps(["அனைத்து பொருட்களையும்", "தன் உடலை மட்டும்", "நட்பை மட்டும்", "கல்வியை மட்டும்"], ensure_ascii=False),
            0,
            "அன்பிலார் எல்லாந் தமக்குரியர் அன்புடையார் என்பும் உரியர் பிறர்க்கு. (குறள் 72)"
        ),
        (
            "Thirukkural", 78, "அன்புடைமை",
            "அன்பில்லாத உயிர்களை அறக்கடவுள் எவ்வாறு தண்டிப்பார்?",
            "How does virtue penalize those devoid of love?",
            json.dumps(["வெயிலில் புழு காய்வது போல", "வெள்ளத்தில் மூழ்குவது போல", "சிறையில் அடைப்பது போல", "சாம்பலாக்குவது போல"], ensure_ascii=False),
            0,
            "என்பி லதனை வெயில்போலக் காயுமே அன்பி லதனை அறம். (குறள் 77)"
        ),
        (
            "Thirukkural", 391, "கல்வி",
            "நூல்களை எவ்வாறு கற்க வேண்டும் என்று திருவள்ளுவர் போதிக்கிறார்?",
            "How should one learn books according to Thiruvalluvar?",
            json.dumps(["மனப்பாடம் மட்டும் செய்ய வேண்டும்", "குற்றமறக் கற்க வேண்டும், கற்றபின் அதன்படி நடக்க வேண்டும்", "வேகமாகப் படிக்க வேண்டும்", "மற்றவர்க்குப் பயிற்றுவிக்க மட்டும் படிக்க வேண்டும்"], ensure_ascii=False),
            1,
            "கற்க கசடறக் கற்பவை கற்றபின் நிற்க அதற்குத் தக. (குறள் 391)"
        ),
        (
            "Thirukkural", 397, "கல்வி",
            "கற்றவருக்கு எந்த நாடும் எந்த ஊரும் எவ்வாறு மாறும்?",
            "How does every town and nation become to an educated person?",
            json.dumps(["அந்நிய நாடாக மாறும்", "தம் சொந்த நாடாகவும் சொந்த ஊராகவும் மாறும்", "அச்சம் தரும் இடமாக மாறும்", "வணிக இடமாக மாறும்"], ensure_ascii=False),
            1,
            "யாதானும் நாடாமால் ஊராமால் என்னொருவன் சாந்துணையுங் கல்லாத வாறு. (குறள் 397)"
        ),
        (
            "Thirukkural", 786, "நட்பு",
            "உண்மை நண்பன் எப்போது உதவ முன்வர வேண்டும்?",
            "When should a true friend step forward to help?",
            json.dumps(["அழைத்த பிறகு மட்டும்", "உடை நழுவும் போது கை உடனே தாங்குவது போல துன்பத்தில் உடனே உதவ வேண்டும்", "மறுநாள் பொறுமையாக", "தனக்கு லாபம் இருக்கும்போது"], ensure_ascii=False),
            1,
            "உடுக்கை இழந்தவன் கைபோல ஆங்கே இடுக்கண் களைவதாம் நட்பு. (குறள் 788)"
        ),
        (
            "Thirukkural", 102, "செய்ந்நன்றியறிதல்",
            "காலத்தினால் செய்த சிறிய உதவி எதனை விடப் பெரியதாகும்?",
            "A help rendered in times of need is greater than what?",
            json.dumps(["கடலை விட", "உலகத்தை விட", "மலையை விட", "ஆகாயத்தை விட"], ensure_ascii=False),
            1,
            "காலத்தினாற்செய்த நன்றி சிறிதெனினும் ஞாலத்தின் மாணப் பெரிது. (குறள் 102)"
        ),
        (
            "Thirukkural", 616, "ஆள்வினையுடைமை",
            "ஊழையும் (விதியையும்) புறமுதுகிட்டு ஓடச் செய்வது எது?",
            "What can overcome fate itself according to Valluvar?",
            json.dumps(["விடாமுயற்சியோடு கூடிய கடின உழைப்பு", "அதிர்ஷ்டம்", "அமைதி", "அதிகாரம்"], ensure_ascii=False),
            0,
            "ஊழையும் உப்பக்கங் காண்பர் உலைவின்றித் தாழாது உஞற்று பவர். (குறள் 620)"
        )
    ]

    cursor.executemany("""
    INSERT INTO quizzes (
        work, kural_number, chapter_name, question_tamil, question_english,
        options_json, correct_index, explanation_tamil
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, quiz_data)
    conn.commit()
    print(f"[+] Seeded {len(quiz_data)} Thirukkural exam prep quiz questions.")

def main():
    print("=" * 60)
    print("Tamil Ilakkiya AI — Database Construction & Ingestion")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    build_schema(conn)
    
    total = 0
    total += ingest_thirukkural(conn)
    total += ingest_sentamizh_work(conn, "Purananuru_All.json", "Purananuru", "Sangam Literature", "சங்கப் புலவர்")
    total += ingest_sentamizh_work(conn, "Akananuru_All.json", "Akananuru", "Sangam Literature", "சங்கப் புலவர்")
    total += ingest_sentamizh_work(conn, "Natrinai_Vaidehi_All.json", "Natrinai", "Sangam Literature", "சங்கப் புலவர்")
    total += ingest_sentamizh_work(conn, "Kuruntokai_Vaidehi_All.json", "Kuruntokai", "Sangam Literature", "சங்கப் புலவர்")
    total += ingest_sentamizh_work(conn, "Silappatikaram_All.json", "Silappathikaram", "Tamil Epics", "இளங்கோவடிகள்")
    total += ingest_sentamizh_work(conn, "Manimekalai_All.json", "Manimekalai", "Tamil Epics", "சீத்தலைச் சாத்தனார்")
    
    seed_thirukkural_quizzes(conn)
    
    # Verification count
    cursor = conn.cursor()
    cursor.execute("SELECT work, count(*) FROM literature_corpus GROUP BY work;")
    counts = cursor.fetchall()
    print("\nCorpus Summary in SQLite Database:")
    for w, c in counts:
        print(f"  - {w:16s}: {c} entries")
    cursor.execute("SELECT count(*) FROM literature_corpus;")
    total_db = cursor.fetchone()[0]
    print(f"\nTotal Canonical Records Indexed: {total_db}")
    print(f"Database successfully saved to: {DB_PATH}")
    print("=" * 60)
    conn.close()

if __name__ == "__main__":
    main()
