"""
test_engine.py
--------------
Tests the 10 varied real questions required by the Hackathon specification.
"""

import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.stdout.reconfigure(encoding='utf-8')
from backend.engine import answer_query

test_questions = [
    ("thirukkural first one", True),
    ("அறம் என்றால் என்ன?", True),
    ("நட்பு என்றால் என்ன?", True),
    ("கல்வி பற்றி வள்ளுவர் என்ன கூறுகிறார்?", True),
    ("புறநானூறு 192 யாதும் ஊரே", True),
    ("What does Thirukkural say about friendship?", True),
    ("சிலப்பதிகாரம் முதல் பாடல்", True),
    ("வான்சிறப்பு மழை பற்றி குறள்", True),
    ("What is quantum computing in Thirukkural?", False),
    ("who won the soccer world cup?", False)
]

all_passed = True
print("=" * 70)
print("TESTING 10 CONSECUTIVE QUERIES ON TAMIL ILAKKIYA AI ENGINE")
print("=" * 70)

for i, (q, should_answer) in enumerate(test_questions, 1):
    res = answer_query(q)
    status = res["status"]
    
    if should_answer and status != "answered":
        print(f"[FAIL] Query {i}: '{q}' was expected to be answered but was {status}")
        all_passed = False
    elif not should_answer and status != "abstained":
        print(f"[FAIL] Query {i}: '{q}' was expected to abstain but was {status}")
        all_passed = False
    else:
        print(f"[PASS] Query {i}: '{q}' -> {status.upper()}")
        if status == "answered":
            ev = res["evidence"]
            print(f"       Citation: {ev['work']} | {ev['chapter']} | Verse #{ev['verse_number']}")
            print(f"       Confidence: {ev['confidence']} | Reason: {ev['match_reason']}")
        else:
            print(f"       Abstention message: {res['message']}")
    print("-" * 70)

print("\n" + "=" * 70)
if all_passed:
    print("[SUCCESS] All 10 queries behaved EXACTLY as expected with 100% compliance!")
else:
    print("[ERROR] Some queries did not match the expected status.")
print("=" * 70)
