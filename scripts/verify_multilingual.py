"""
verify_multilingual.py
-----------------------
Automated verification for Tamil, English, and Hindi multilingual answer generation,
strict schema validation, unsupported responses, HTTP 400 rejection, and follow-up queries.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.stdout.reconfigure(encoding='utf-8')

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_multilingual():
    print("=" * 70)
    print("VERIFYING MULTILINGUAL TAMIL ILAKKIYA AI PIPELINE")
    print("=" * 70)

    # 1. Tamil Query
    r = client.post('/query', json={'question': 'நட்பைப் பற்றி திருக்குறள் என்ன கூறுகிறது?', 'language': 'ta'})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    d = r.json()
    assert d["supported"] is True
    assert len(d["citations"]) > 0
    assert d["citations"][0] == "Thirukkural · Kural 781"
    assert "திருவள்ளுவர்" in d["answer"]
    print(f"[PASS] 1. Tamil Query (நட்பு) -> Supported: True, Citation: {d['citations'][0]}")

    # 2. English Query
    r = client.post('/query', json={'question': 'What does Thirukkural say about friendship?', 'language': 'en'})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    d = r.json()
    assert d["supported"] is True
    assert len(d["citations"]) > 0
    assert d["citations"][0] == "Thirukkural · Kural 781"
    assert "Thiruvalluvar" in d["answer"] or "friendship" in d["answer"].lower()
    print(f"[PASS] 2. English Query (Friendship) -> Supported: True, Citation: {d['citations'][0]}")

    # 3. Hindi Query
    r = client.post('/query', json={'question': 'तिरुक्कुरल मित्रता के बारे में क्या कहता है?', 'language': 'hi'})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    d = r.json()
    assert d["supported"] is True
    assert len(d["citations"]) > 0
    assert d["citations"][0] == "Thirukkural · Kural 781"
    assert "तिरुवल्लुवर" in d["answer"] or "मित्रता" in d["answer"]
    print(f"[PASS] 3. Hindi Query (मित्रता) -> Supported: True, Citation: {d['citations'][0]}")

    # 4. Canonical Authorship Query
    r = client.post('/query', json={'question': 'who wrote thirukkural?', 'language': 'en'})
    assert r.status_code == 200
    d = r.json()
    assert d["supported"] is True
    assert "Thiruvalluvar" in d["answer"]
    print(f"[PASS] 4. Authorship Query (who wrote thirukkural) -> Thiruvalluvar verified in citation {d['citations']}")

    # 5. Invalid Language Code HTTP 400
    r = client.post('/query', json={'question': 'What is virtue?', 'language': 'fr'})
    assert r.status_code == 400, f"Expected 400, got {r.status_code}"
    print(f"[PASS] 5. Invalid Language ('fr') correctly rejected with HTTP 400")

    # 6. Unsupported Questions in all 3 languages
    unsupported_specs = {
        "ta": "வழங்கப்பட்ட ஆதாரங்களில் இந்த தகவல் கிடைக்கவில்லை.",
        "en": "The information is not available in the provided sources.",
        "hi": "प्रदान किए गए स्रोतों में यह जानकारी उपलब्ध नहीं है।"
    }

    for lang, expected_msg in unsupported_specs.items():
        r = client.post('/query', json={'question': 'What is quantum physics in black holes?', 'language': lang})
        assert r.status_code == 200
        d = r.json()
        assert d["supported"] is False, f"Expected supported=False for lang={lang}"
        assert d["citations"] == [], f"Expected empty citations for lang={lang}"
        assert d["answer"] == expected_msg, f"Expected '{expected_msg}', got '{d['answer']}'"
        print(f"[PASS] 6. Unsupported Query in '{lang}' -> Matched exact requirement message: '{d['answer']}'")

    # 7. Follow-up Query with session_id
    sess_id = "test-session-101"
    # First query in English
    r1 = client.post('/query', json={'question': 'tell me about friendship in thirukkural', 'language': 'en', 'session_id': sess_id})
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["supported"] is True

    # Follow-up in Hindi
    r2 = client.post('/query', json={'question': 'explain this meaning in more detail', 'language': 'hi', 'session_id': sess_id})
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["supported"] is True
    assert d2["citations"][0] == d1["citations"][0]
    assert "तिरुवल्लुवर" in d2["answer"] or "मित्रता" in d2["answer"]
    print(f"[PASS] 7. Follow-up query in Hindi via session_id -> Resolved prior verse and answered in Hindi")

    # 8. Endpoints /health, /works, and /retrieve
    r_health = client.get('/health')
    assert r_health.status_code == 200
    assert r_health.json()["database_ready"] is True
    print(f"[PASS] 8a. /health verified -> Total records: {r_health.json()['total_canonical_records']}")

    r_works = client.get('/works')
    assert r_works.status_code == 200
    assert r_works.json()["total_works"] == 7
    print(f"[PASS] 8b. /works verified -> All 7 works returned")

    r_ret = client.post('/retrieve', json={'question': 'நட்பு', 'top_k': 3})
    assert r_ret.status_code == 200
    results = r_ret.json()["results"]
    assert len(results) > 0
    print(f"[PASS] 8c. /retrieve verified -> Retrieved {len(results)} literature candidates with citations")

    # 9. Response schema strictness test
    keys = set(d.keys())
    assert keys == {"supported", "answer", "citations"}, f"Unexpected keys in response: {keys}"
    print(f"[PASS] 9. Response schema strictly verified: {sorted(list(keys))}")

    print("\n" + "=" * 70)
    print("ALL MULTILINGUAL SYSTEM VERIFICATIONS PASSED 100%!")
    print("=" * 70)

if __name__ == "__main__":
    test_multilingual()
