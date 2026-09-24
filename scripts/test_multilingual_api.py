"""
test_multilingual_api.py
Comprehensive test suite verifying backend multilingual endpoints.
"""

import urllib.request
import urllib.error
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def get(path):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))

def post(path, payload, expect_status=200):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = body
        return e.code, parsed

def run_tests():
    print("=== RUNNING MULTILINGUAL TEST SUITE ===")
    
    # Test 1: Poems listing multilingual schema
    print("\n[Test 1] GET /api/literature/poems?limit=3")
    res1 = get("/api/literature/poems?limit=3")
    assert "poems" in res1 and len(res1["poems"]) == 3, f"Failed poems: {res1}"
    p = res1["poems"][0]
    for key in ["title", "content", "meaning", "author"]:
        assert key in p and isinstance(p[key], dict), f"Missing dict key {key} in {p}"
        assert "ta" in p[key] and "en" in p[key] and "hi" in p[key], f"Missing lang in {key}: {p[key]}"
    print("  -> Passed. First poem title: ta='%s', en='%s', hi='%s'" % (p["title"]["ta"], p["title"]["en"], p["title"]["hi"]))

    # Test 2: Search in English
    print("\n[Test 2] GET /api/literature/poems?search=friendship")
    res2 = get("/api/literature/poems?search=friendship&limit=5")
    assert res2["total"] > 0, "No results for English search 'friendship'"
    print(f"  -> Passed. Found {res2['total']} results for 'friendship'")

    # Test 3: Search in Hindi
    print("\n[Test 3] GET /api/literature/poems?search=मित्रता")
    res3 = get("/api/literature/poems?search=" + urllib.parse.quote("मित्रता") + "&limit=5")
    assert res3["total"] > 0, "No results for Hindi search 'मित्रता'"
    print(f"  -> Passed. Found {res3['total']} results for 'मित्रता'")

    # Test 4: Thirukkural Chapters
    print("\n[Test 4] GET /api/literature/thirukkural/chapters")
    res4 = get("/api/literature/thirukkural/chapters")
    assert "sections" in res4 and len(res4["sections"]) == 3
    sec0 = res4["sections"][0]
    assert "paal_en" in sec0 and "paal_hi" in sec0
    ch0 = sec0["chapters"][0]
    assert "title_english" in ch0 and "title_hindi" in ch0
    print("  -> Passed. Section 0: '%s' / '%s' / '%s', Ch 0: '%s' / '%s'" % (sec0["paal"], sec0["paal_en"], sec0["paal_hi"], ch0["chapter_name"], ch0["title_english"]))

    # Test 5: Thirukkural Chapter 1 Kurals
    print("\n[Test 5] GET /api/literature/thirukkural/chapter/1")
    res5 = get("/api/literature/thirukkural/chapter/1")
    assert len(res5["kurals"]) == 10
    k1 = res5["kurals"][0]
    assert k1["kural"]["en"] and k1["kural"]["hi"]
    print("  -> Passed. Kural 1 English: '%s'" % k1["kural"]["en"][:60])
    print("  -> Passed. Kural 1 Hindi: '%s'" % k1["kural"]["hi"][:60])

    # Test 6: Thirukkural Compare Tool
    print("\n[Test 6] GET /api/literature/thirukkural/compare?kural1=1&kural2=391")
    res6 = get("/api/literature/thirukkural/compare?kural1=1&kural2=391")
    assert "difference_analysis_multilingual" in res6
    assert "en" in res6["difference_analysis_multilingual"]
    assert "hi" in res6["difference_analysis_multilingual"]
    print("  -> Passed. Multilingual comparative analysis available.")

    # Test 7: /query endpoint validation - HTTP 400 on unsupported language
    print("\n[Test 7] POST /query with language='fr' (Expect HTTP 400)")
    status, res7 = post("/query", {"question": "Hello", "language": "fr"})
    assert status == 400, f"Expected 400, got {status}: {res7}"
    print("  -> Passed. HTTP 400 correctly rejected invalid language.")

    # Test 8: /query in English
    print("\n[Test 8] POST /query with language='en'")
    status, res8 = post("/query", {"question": "What is the meaning of friendship in Thirukkural?", "language": "en"})
    assert status == 200, f"Failed: {res8}"
    assert "answer" in res8 and len(res8["answer"]) > 10
    print("  -> Passed. English answer preview: %s..." % res8["answer"][:80].replace("\n", " "))

    # Test 9: /query in Hindi
    print("\n[Test 9] POST /query with language='hi'")
    status, res9 = post("/query", {"question": "तिरुक्कुरल के अनुसार मित्रता क्या है?", "language": "hi"})
    assert status == 200, f"Failed: {res9}"
    assert "answer" in res9 and len(res9["answer"]) > 10
    print("  -> Passed. Hindi answer preview: %s..." % res9["answer"][:80].replace("\n", " "))

    # Test 10: Authorship query in English
    print("\n[Test 10] POST /query with 'who wrote thirukkural' in English")
    status, res10 = post("/query", {"question": "who wrote thirukkural", "language": "en"})
    assert status == 200
    assert "Thiruvalluvar" in res10["answer"]
    print("  -> Passed. Correctly identified Thiruvalluvar in English.")

    # Test 11: /api/query rich endpoint returns evidence with text_english and text_hindi
    print("\n[Test 11] POST /api/query with language='en' (Rich evidence)")
    status, res11 = post("/api/query", {"question": "friendship", "language": "en"})
    assert status == 200
    assert "evidence" in res11 and res11["evidence"]
    ev = res11["evidence"]
    assert "text_english" in ev or "meaning_english" in ev
    print("  -> Passed. Evidence text_english: %s..." % (ev.get("text_english") or ev.get("meaning_english"))[:60])

    print("\n=== ALL 11 TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_tests()
