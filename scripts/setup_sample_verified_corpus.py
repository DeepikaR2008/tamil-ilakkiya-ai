"""
setup_sample_verified_corpus.py
-------------------------------
Helper script to populate data/raw/ with canonical sample records for all 7 works
matching the exact required schemas, so that developers can test cleaning,
validation, and ChromaDB retrieval immediately.
"""

import json
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

SAMPLE_DATA = {
    "thirukkural": [
        {
            "id": "thirukkural_1",
            "text": "அகர முதல எழுத்தெல்லாம் ஆதி\nபகவன் முதற்றே உலகு.",
            "metadata": {
                "work": "Thirukkural",
                "section": "Aram",
                "chapter_number": 1,
                "chapter_name": "கடவுள் வாழ்த்து",
                "verse_number": 1,
                "poet": "திருவள்ளுவர்",
                "literary_type": "Kural"
            }
        },
        {
            "id": "thirukkural_2",
            "text": "கற்றதனால் ஆய பயன்கொல் வாலறிவன்\nநற்றாள் தொழாஅர் எனின்.",
            "metadata": {
                "work": "Thirukkural",
                "section": "Aram",
                "chapter_number": 1,
                "chapter_name": "கடவுள் வாழ்த்து",
                "verse_number": 2,
                "poet": "திருவள்ளுவர்",
                "literary_type": "Kural"
            }
        },
        {
            "id": "thirukkural_391",
            "text": "கற்க கசடறக் கற்பவை கற்றபின்\nநிற்க அதற்குத் தக.",
            "metadata": {
                "work": "Thirukkural",
                "section": "Porul",
                "chapter_number": 40,
                "chapter_name": "கல்வி",
                "verse_number": 391,
                "poet": "திருவள்ளுவர்",
                "literary_type": "Kural"
            }
        }
    ],
    "purananuru": [
        {
            "id": "purananuru_1",
            "text": "கண்ணி கார்நறுங் கொன்றை காமர்\nவண்ண மார்பிற் றாரும் கொன்றை\nஊர்தி வால்வெள் ளேறே சிறந்த\nசீர்கெழு கொடியும் அவ்வே றென்ப.",
            "metadata": {
                "work": "Purananuru",
                "poem_number": 1,
                "verse_number": 1,
                "poet": "பாரதம் பாடிய பெருந்தேவனார்",
                "thematic_category": "கடவுள் வாழ்த்து",
                "literary_type": "Sangam Poem"
            }
        },
        {
            "id": "purananuru_182",
            "text": "உண்டால் அம்ம இவ்வுலகம் இந்திரர்\nஅமிழ்தம் இயைவது ஆயினும் இனிதுஎனத்\nதமியர் உண்டலும் இலரே முனிவிலர்\nதுஞ்சலும் இலர்பிறர் அஞ்சுவது அஞ்சி.",
            "metadata": {
                "work": "Purananuru",
                "poem_number": 182,
                "verse_number": 182,
                "poet": "கடலுள் மாய்ந்த இளம்பெருவழுதி",
                "thematic_category": "பொதுவியல்",
                "literary_type": "Sangam Poem"
            }
        }
    ],
    "akananuru": [
        {
            "id": "akananuru_1",
            "text": "திதலை மகடூஉச் சிலம்பொலி கேட்பத்\nபுதல்வர் தாயே புல்லோற் போல\nநெஞ்சம் கலங்கக் காணாள் கண்ணீர்\nமல்கினள் உறைவோள் மார்புறத் தழீஇ.",
            "metadata": {
                "work": "Akananuru",
                "poem_number": 1,
                "verse_number": 1,
                "poet": "பெருங்குன்றூர் கிழார்",
                "thematic_category": "பாலை",
                "literary_type": "Sangam Poem"
            }
        }
    ],
    "natrinai": [
        {
            "id": "natrinai_1",
            "text": "மாநிலம் சேவடியாகத் தூநீர்\nவளைநரல் பௌவம் உடுக்கையாக\nவிசும்புமெய் யாகத் திசைகையா க\nஇருசுடர் விழியாக இயன்ற எல்லாம்.",
            "metadata": {
                "work": "Natrinai",
                "poem_number": 1,
                "verse_number": 1,
                "poet": "பாரதம் பாடிய பெருந்தேவனார்",
                "thematic_category": "கடவுள் வாழ்த்து",
                "literary_type": "Sangam Poem"
            }
        }
    ],
    "kuruntokai": [
        {
            "id": "kuruntokai_1",
            "text": "செம்புலப் பெயல்நீர் போல\nஅன்புடை நெஞ்சம் தாம் கலந்தனவே.",
            "metadata": {
                "work": "Kuruntokai",
                "poem_number": 1,
                "verse_number": 1,
                "poet": "செம்புலப் பெயனீரார்",
                "thematic_category": "குறிஞ்சி",
                "literary_type": "Sangam Poem"
            }
        }
    ],
    "silappathikaram": [
        {
            "id": "silappathikaram_1_1",
            "text": "திங்களைப் போற்றுதும் திங்களைப் போற்றுதும்\nகொங்கலர் தண்தார்க் குளிர்வெண் குடைபோன்றிவ்\nவங்கண் உலக்களித்த லான்.",
            "metadata": {
                "work": "Silappathikaram",
                "kandam": "புகார்க் காண்டம்",
                "kaathai": "மங்கல வாழ்த்துப் பாடல்",
                "chapter_number": 1,
                "verse_or_section": "1-3",
                "poet": "இளங்கோவடிகள்",
                "literary_type": "Epic"
            }
        }
    ],
    "manimekalai": [
        {
            "id": "manimekalai_1_1",
            "text": "தெய்வந் தொழாஅள் கொழுநற் றொழுதெழுவாள்\nபெய்யெனப் பெய்யும் மழை.",
            "metadata": {
                "work": "Manimekalai",
                "kaathai": "விழாவறை காதை",
                "chapter_number": 1,
                "verse_or_section": "1-5",
                "poet": "சீத்தலைச் சாத்தனார்",
                "literary_type": "Epic"
            }
        }
    ]
}

def setup_sample_files():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for work_name, records in SAMPLE_DATA.items():
        file_path = RAW_DIR / f"{work_name}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        print(f"[+] Sample raw file created: {file_path}")

if __name__ == "__main__":
    setup_sample_files()
