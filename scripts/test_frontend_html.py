"""
test_frontend_html.py
Verifies that index.html served at root contains the latest multilingual logic.
"""

import urllib.request

url = "http://127.0.0.1:8000/"
with urllib.request.urlopen(url) as r:
    html = r.read().decode("utf-8")

checks = [
    "getMultilingualField(p, 'content', 'en')",
    "getMultilingualField(p, 'content', 'hi')",
    "getMultilingualField(k, 'kural', 'en')",
    "getMultilingualField(k, 'kural', 'hi')",
    "btn-lang-hi",
    "setLanguage(state.lang)",
    "difference_analysis_multilingual",
    "English translation unavailable",
    "हिन्दी अनुवाद उपलब्ध नहीं है"
]

print("Checking index.html served at root:")
for c in checks:
    assert c in html, f"Missing check in served HTML: {c}"
    print(f"  [x] Contains: '{c}'")

print("\nFrontend HTML verification 100% successful!")
