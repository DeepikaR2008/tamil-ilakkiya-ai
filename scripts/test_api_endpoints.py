"""
test_api_endpoints.py
---------------------
Full automated verification suite for all API routes, authentication,
retrieval engine, and database persistence.
"""

import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.stdout.reconfigure(encoding='utf-8')

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def run_tests():
    print("=" * 70)
    print("TAMIL ILAKKIYA AI — FULL END-TO-END SYSTEM TEST")
    print("=" * 70)

    # 1. Health check
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["database_ready"] is True
    print(f"[PASS] 1. Health Check OK — Total Canonical Records: {data['total_canonical_records']}")

    # 2. Frontend HTML delivery
    res = client.get("/")
    assert res.status_code == 200
    assert "Tamil Ilakkiya AI" in res.text
    print("[PASS] 2. Web UI Delivery (index.html) OK")

    # 3. Works endpoint
    res = client.get("/api/literature/works")
    assert res.status_code == 200
    works_data = res.json()
    assert works_data["total_works"] == 7
    print(f"[PASS] 3. Canonical Works Endpoint OK — All {works_data['total_works']} works returned")

    # 4. Thirukkural 133 Chapters
    res = client.get("/api/literature/thirukkural/chapters")
    assert res.status_code == 200
    ch_data = res.json()
    total_chapters = sum(sec["count"] for sec in ch_data["sections"])
    assert total_chapters == 133
    print(f"[PASS] 4. Thirukkural Chapters OK — Exactly {total_chapters} Adhikarams verified across 3 Paals")

    # 5. Kural Compare Tool
    res = client.get("/api/literature/thirukkural/compare?kural1=1&kural2=391")
    assert res.status_code == 200
    cmp_data = res.json()
    assert cmp_data["kural_1"]["verse_number"] == 1
    assert cmp_data["kural_2"]["verse_number"] == 391
    print("[PASS] 5. Kural Side-by-Side Compare Tool OK")

    # 6. Exam Quiz endpoint
    res = client.get("/api/literature/thirukkural/quiz")
    assert res.status_code == 200
    quizzes = res.json()["quizzes"]
    assert len(quizzes) > 0
    print(f"[PASS] 6. Exam Quiz Endpoint OK — {len(quizzes)} curated exam prep questions available")

    # 7. Ask-AI Valid Query (Kural 1)
    res = client.post("/api/query", json={"query": "thirukkural first one", "language": "ta"})
    assert res.status_code == 200
    q1_data = res.json()
    assert q1_data["status"] == "answered"
    assert q1_data["evidence"]["verse_number"] == 1
    print(f"[PASS] 7. Ask-AI Query (thirukkural first one) -> Answered with Kural 1 (Conf: {q1_data['evidence']['confidence']})")

    # 8. Ask-AI Concept Query (நட்பு)
    res = client.post("/api/query", json={"query": "நட்பு என்றால் என்ன?", "language": "ta"})
    assert res.status_code == 200
    q2_data = res.json()
    assert q2_data["status"] == "answered"
    assert "நட்பு" in q2_data["evidence"]["chapter"]
    print(f"[PASS] 8. Ask-AI Concept Query (நட்பு) -> Answered with Natpu verse (Conf: {q2_data['evidence']['confidence']})")

    # 9. Ask-AI Out-of-Domain Abstention
    res = client.post("/api/query", json={"query": "what is quantum computing in thirukkural?", "language": "en"})
    assert res.status_code == 200
    q3_data = res.json()
    assert q3_data["status"] == "abstained"
    print("[PASS] 9. Ask-AI Abstention Gate OK -> Accurately abstained without hallucinating")

    # 10. User Registration & Session
    test_email = "tamil_student@example.com"
    test_pw = "pass12345"
    client.post("/api/auth/register", json={"email": test_email, "password": test_pw, "name": "Deepika"})
    res = client.post("/api/auth/login", json={"email": test_email, "password": test_pw})
    assert res.status_code == 200
    login_data = res.json()
    assert login_data["success"] is True
    token = login_data["token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[PASS] 10. User Registration & Login OK — Persistent session token issued")

    # 11. Bookmarking
    res = client.post("/api/user/bookmarks", json={"verse_id": "thirukkural_391", "work": "Thirukkural", "verse_number": 391}, headers=headers)
    assert res.status_code == 200
    res = client.get("/api/user/bookmarks", headers=headers)
    assert res.status_code == 200
    b_data = res.json()
    assert len(b_data["bookmarks"]) >= 1
    print(f"[PASS] 11. Bookmarking OK — Saved {b_data['bookmarks'][0]['work']} #{b_data['bookmarks'][0]['verse_number']}")

    # 12. History Persistence & Clear
    client.post("/api/query", json={"query": "கல்வி பற்றி குறள்", "language": "ta"}, headers=headers)
    res = client.get("/api/user/history", headers=headers)
    assert res.status_code == 200
    hist = res.json()["history"]
    assert len(hist) >= 1
    print(f"[PASS] 12. History Persistence OK — Recorded question '{hist[0]['question']}'")

    res = client.delete("/api/user/history", headers=headers)
    assert res.status_code == 200
    res = client.get("/api/user/history", headers=headers)
    assert len(res.json()["history"]) == 0
    print("[PASS] 13. History Deletion OK — User successfully cleared history")

    print("\n" + "=" * 70)
    print("ALL 13 SYSTEM INTEGRATION TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
