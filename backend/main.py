"""
main.py
-------
FastAPI Backend for Tamil Ilakkiya AI.
Provides complete 5-Page endpoints:
1. Auth & Session Management (Login, Signup, Reset, Me)
2. Ask-AI Bilingual Citation-Grounded Chatbot & Poem-Specific Q&A
3. All-Poems Explorer across 7 canonical works
4. Thirukkural Dedicated Chapter Explorer, Compare Tool, and Student Quiz
5. User History & Bookmarks Persistence
"""

import sys
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, HTTPException, Header, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from backend.engine import (
    answer_query,
    answer_poem_specific_query,
    get_db_connection,
    search_corpus_hybrid,
    make_citation,
    DB_PATH
)
from backend.auth import (
    register_user,
    login_user,
    reset_password,
    get_current_user
)

app = FastAPI(
    title="Tamil Ilakkiya AI — Production Backend",
    description="Evidence-First, Citation-Grounded Assistant for Classical Tamil Literature",
    version="2.0.0"
)

# Enable CORS for all devices (mobile, tablet, desktop, LAN)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure static directories exist
STATIC_DIR = ROOT_DIR / "frontend" / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)


# --- Dependency: Optional Authenticated User ---
def get_user_from_header(authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    if not authorization:
        return None
    token = authorization.replace("Bearer ", "").strip()
    return get_current_user(token)


# --- Request / Response Models ---
class QueryRequest(BaseModel):
    query: Optional[str] = None
    question: Optional[str] = None
    language: Optional[str] = "ta"
    work: Optional[str] = None
    work_filter: Optional[str] = None
    session_id: Optional[str] = None
    top_k: Optional[int] = 5

class RetrieveRequest(BaseModel):
    query: Optional[str] = None
    question: Optional[str] = None
    work: Optional[str] = None
    work_filter: Optional[str] = None
    top_k: Optional[int] = 5

class PoemQueryRequest(BaseModel):
    poem_id: str
    question: str
    language: Optional[str] = "ta"

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class ResetRequest(BaseModel):
    email: str
    new_password: str

class BookmarkRequest(BaseModel):
    verse_id: str
    work: str
    verse_number: Any


# =====================================================================
# 1. FRONTEND ROUTE
# =====================================================================
@app.get("/")
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        # Fallback to backend static if present
        fallback = ROOT_DIR / "backend" / "static" / "index.html"
        if fallback.exists():
            return FileResponse(str(fallback))
        return JSONResponse({"status": "Frontend not ready yet."})
    return FileResponse(str(index_file))


# =====================================================================
# 2. ASK-AI QUERY ENDPOINT (Contract §7.1)
# =====================================================================
@app.post("/query")
def handle_query_strict(req: QueryRequest, user: Optional[Dict[str, Any]] = Depends(get_user_from_header)):
    """
    Standard Ask-AI Query Endpoint.
    Strictly accepts ta, en, hi; rejects any other language with HTTP 400.
    Strictly returns: {"supported": bool, "answer": str, "citations": list[str]}
    """
    if req.language not in ("ta", "en", "hi"):
        raise HTTPException(status_code=400, detail="Invalid language. Supported languages: ta, en, hi")

    raw_q = (req.question or req.query or "").strip()
    wf = req.work or req.work_filter
    top_k = req.top_k or 5

    result = answer_query(
        raw_q,
        requested_lang=req.language,
        work_filter=wf,
        session_id=req.session_id,
        top_k=top_k
    )

    # Save to user history if logged in
    if user and raw_q:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            ev = result.get("evidence") or {}
            cursor.execute("""
                INSERT INTO history (user_id, question, answer, citation, verse_id, work, confidence, language)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                user["id"],
                raw_q,
                result.get("answer") or result.get("message") or "Abstained",
                f"{ev.get('work', '')} #{ev.get('verse_number', '')}" if ev else None,
                ev.get("verse_id"),
                ev.get("work"),
                ev.get("confidence", 0.0),
                req.language
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[!] Error saving history: {e}")

    return {
        "supported": result.get("supported", False),
        "answer": result.get("answer", ""),
        "citations": result.get("citations", [])
    }


@app.post("/api/query")
def handle_query_api(req: QueryRequest, user: Optional[Dict[str, Any]] = Depends(get_user_from_header)):
    """
    Ask-AI endpoint for rich frontend UI.
    Validates ta, en, hi; returns full object including evidence, palm-leaf motif metadata, and citations.
    """
    if req.language not in ("ta", "en", "hi"):
        raise HTTPException(status_code=400, detail="Invalid language. Supported languages: ta, en, hi")

    raw_q = (req.question or req.query or "").strip()
    wf = req.work or req.work_filter
    top_k = req.top_k or 5

    result = answer_query(
        raw_q,
        requested_lang=req.language,
        work_filter=wf,
        session_id=req.session_id,
        top_k=top_k
    )

    # Save to user history if logged in
    if user and raw_q:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            ev = result.get("evidence") or {}
            cursor.execute("""
                INSERT INTO history (user_id, question, answer, citation, verse_id, work, confidence, language)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                user["id"],
                raw_q,
                result.get("answer") or result.get("message") or "Abstained",
                f"{ev.get('work', '')} #{ev.get('verse_number', '')}" if ev else None,
                ev.get("verse_id"),
                ev.get("work"),
                ev.get("confidence", 0.0),
                req.language
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[!] Error saving history: {e}")

    return result


@app.get("/retrieve")
@app.post("/retrieve")
def handle_retrieve(
    req: Optional[RetrieveRequest] = None,
    query: Optional[str] = Query(None),
    question: Optional[str] = Query(None),
    work: Optional[str] = Query(None),
    top_k: int = Query(5)
):
    """
    Standalone RAG retrieval endpoint.
    Retrieves top literature candidates with confidence scores and canonical citations.
    """
    q = ""
    target_work = None
    k = top_k
    if req:
        q = (req.question or req.query or "").strip()
        target_work = req.work or req.work_filter
        if req.top_k:
            k = req.top_k
    if not q:
        q = (question or query or "").strip()
        if work:
            target_work = work

    if not q:
        return {"query": "", "results": []}

    scored = search_corpus_hybrid(q, work_filter=target_work, top_k=k)
    results = []
    for rec, conf, reason in scored:
        results.append({
            "verse_id": rec["id"],
            "work": rec["work"],
            "chapter_name": rec.get("chapter_name"),
            "verse_number": rec.get("verse_number"),
            "text_tamil": rec.get("text_tamil"),
            "explanation_tamil": rec.get("explanation_tamil"),
            "explanation_english": rec.get("explanation_english"),
            "citation": make_citation(rec["work"], rec.get("verse_number")),
            "confidence": conf,
            "reason": reason
        })
    return {"query": q, "results": results}


@app.post("/api/poem-query")
def handle_poem_query(req: PoemQueryRequest, user: Optional[Dict[str, Any]] = Depends(get_user_from_header)):
    """In-context Q&A for an individual poem on Page 3 or Page 4."""
    result = answer_poem_specific_query(req.poem_id, req.question, req.language)
    if user and result.get("status") == "answered":
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            ev = result.get("evidence") or {}
            cursor.execute("""
                INSERT INTO history (user_id, question, answer, citation, verse_id, work, confidence, language)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                user["id"],
                f"[{ev.get('work')} #{ev.get('verse_number')}]: {req.question}",
                result.get("answer", ""),
                f"{ev.get('work')} #{ev.get('verse_number')}",
                req.poem_id,
                ev.get("work"),
                0.98,
                result.get("language", "ta")
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[!] Error saving poem history: {e}")
    return result


# =====================================================================
# 3. LITERATURE EXPLORER & WORKS API (Page 2 & Page 3)
# =====================================================================
@app.get("/works")
@app.get("/api/literature/works")
def get_canonical_works():
    """Returns the 7 canonical works grouped into Sangam Literature & Epics."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT work, group_name, COUNT(*) as count 
        FROM literature_corpus 
        GROUP BY work 
        ORDER BY count DESC;
    """)
    rows = cursor.fetchall()
    conn.close()

    sangam = []
    epics = []
    for r in rows:
        item = {
            "work": r["work"],
            "count": r["count"],
            "group": r["group_name"]
        }
        if r["group_name"] == "Tamil Epics":
            epics.append(item)
        else:
            sangam.append(item)

    return {
        "groups": [
            {"title": "Sangam Literature", "title_ta": "சங்க இலக்கியம்", "works": sangam},
            {"title": "Tamil Epics", "title_ta": "தமிழ் காப்பியங்கள்", "works": epics}
        ],
        "total_works": len(rows)
    }


@app.get("/api/literature/poems")
def list_poems(
    work: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Browses poems across all 7 works with clean Tamil text and explanations."""
    conn = get_db_connection()
    cursor = conn.cursor()

    conditions = []
    params = []

    if work and work.lower() != "all":
        conditions.append("work = ?")
        params.append(work)

    if search and search.strip():
        kw = f"%{search.strip().lower()}%"
        conditions.append("(search_tokens LIKE ? OR text_tamil LIKE ? OR chapter_name LIKE ?)")
        params.extend([kw, kw, kw])

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    # Count total
    cursor.execute(f"SELECT COUNT(*) FROM literature_corpus {where_clause};", params)
    total_count = cursor.fetchone()[0]

    # Fetch paginated items
    sql = f"""
        SELECT id, work, group_name, section, chapter_number, chapter_name,
               verse_number, poet, text_tamil, text_transliteration,
               explanation_tamil, explanation_english, theme
        FROM literature_corpus
        {where_clause}
        ORDER BY work, verse_number ASC
        LIMIT ? OFFSET ?;
    """
    cursor.execute(sql, params + [limit, offset])
    rows = cursor.fetchall()
    conn.close()

    return {
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "poems": [dict(r) for r in rows]
    }


@app.get("/api/literature/poem/{poem_id}")
def get_poem_by_id(poem_id: str):
    """Fetches a single poem with full citation and context."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM literature_corpus WHERE id = ? LIMIT 1;", (poem_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Poem not found")
    return dict(row)


# =====================================================================
# 4. THIRUKKURAL DEDICATED API (Page 4)
# =====================================================================
@app.get("/api/literature/thirukkural/chapters")
def get_thirukkural_chapters():
    """Returns all 133 Adhikarams grouped by Paal."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT chapter_number, chapter_name, section,
               MIN(verse_number) as start_kural,
               MAX(verse_number) as end_kural
        FROM literature_corpus
        WHERE work = 'Thirukkural'
        GROUP BY chapter_number
        ORDER BY chapter_number ASC;
    """)
    rows = cursor.fetchall()
    conn.close()

    paals = {"அறத்துப்பால்": [], "பொருட்பால்": [], "காமத்துப்பால்": []}
    for r in rows:
        sec = r["section"] or "அறத்துப்பால்"
        if sec in paals:
            paals[sec].append(dict(r))
        else:
            paals["அறத்துப்பால்"].append(dict(r))

    return {
        "sections": [
            {"paal": "அறத்துப்பால்", "paal_en": "Aram (Virtue)", "count": len(paals["அறத்துப்பால்"]), "chapters": paals["அறத்துப்பால்"]},
            {"paal": "பொருட்பால்", "paal_en": "Porul (Wealth & Politics)", "count": len(paals["பொருட்பால்"]), "chapters": paals["பொருட்பால்"]},
            {"paal": "காமத்துப்பால்", "paal_en": "Inbam (Love & Emotion)", "count": len(paals["காமத்துப்பால்"]), "chapters": paals["காமத்துப்பால்"]}
        ]
    }


@app.get("/api/literature/thirukkural/chapter/{chapter_number}")
def get_kurals_by_chapter(chapter_number: int):
    """Returns the 10 Kurals for a given Adhikaram."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM literature_corpus
        WHERE work = 'Thirukkural' AND chapter_number = ?
        ORDER BY verse_number ASC;
    """, (chapter_number,))
    rows = cursor.fetchall()
    conn.close()
    return {"chapter_number": chapter_number, "kurals": [dict(r) for r in rows]}


@app.get("/api/literature/thirukkural/compare")
def compare_kurals(kural1: int = Query(1), kural2: int = Query(391)):
    """Side-by-side comparison tool for two Kurals."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM literature_corpus WHERE work = 'Thirukkural' AND verse_number IN (?, ?);", (kural1, kural2))
    rows = cursor.fetchall()
    conn.close()

    map_k = {r["verse_number"]: dict(r) for r in rows}
    k1 = map_k.get(kural1)
    k2 = map_k.get(kural2)

    if not k1 or not k2:
        raise HTTPException(status_code=404, detail="One or both Kural numbers not found.")

    diff_analysis = (
        f"குறள் {k1['verse_number']} ({k1['chapter_name']}) '{k1['section']}' நெறியிலும், "
        f"குறள் {k2['verse_number']} ({k2['chapter_name']}) '{k2['section']}' நெறியிலும் அமைந்தவை. "
        f"இரண்டும் திருவள்ளுவரின் ஆழமான வாழ்வியல் பார்வையின் வெவ்வேறு பரிமாணங்களை விளக்குகின்றன."
    )

    return {
        "kural_1": k1,
        "kural_2": k2,
        "difference_analysis": diff_analysis
    }


@app.get("/api/literature/thirukkural/quiz")
def get_quiz_questions():
    """Returns interactive quiz questions based on Thirukkural for exam prep."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, kural_number, chapter_name, question_tamil, question_english, options_json, correct_index, explanation_tamil FROM quizzes;")
    rows = cursor.fetchall()
    conn.close()

    import json
    quizzes = []
    for r in rows:
        quizzes.append({
            "id": r["id"],
            "kural_number": r["kural_number"],
            "chapter_name": r["chapter_name"],
            "question_tamil": r["question_tamil"],
            "question_english": r["question_english"],
            "options": json.loads(r["options_json"]),
            "correct_index": r["correct_index"],
            "explanation": r["explanation_tamil"]
        })
    return {"quizzes": quizzes}


# =====================================================================
# 5. USER AUTH & SESSIONS (Page 1)
# =====================================================================
@app.post("/api/auth/register")
def handle_register(req: RegisterRequest):
    return register_user(req.email, req.password, req.name)


@app.post("/api/auth/login")
def handle_login(req: LoginRequest):
    return login_user(req.email, req.password)


@app.post("/api/auth/reset-password")
def handle_reset_password(req: ResetRequest):
    return reset_password(req.email, req.new_password)


@app.get("/api/auth/me")
def handle_get_me(user: Optional[Dict[str, Any]] = Depends(get_user_from_header)):
    if not user:
        return {"authenticated": False, "user": None}
    return {"authenticated": True, "user": user}


# =====================================================================
# 6. USER HISTORY & BOOKMARKS (Page 5)
# =====================================================================
@app.get("/api/user/history")
def get_history(user: Optional[Dict[str, Any]] = Depends(get_user_from_header)):
    if not user:
        raise HTTPException(status_code=401, detail="Please log in to view history.")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, question, answer, citation, verse_id, work, confidence, created_at 
        FROM history 
        WHERE user_id = ? 
        ORDER BY created_at DESC;
    """, (user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return {"history": [dict(r) for r in rows]}


@app.delete("/api/user/history")
def clear_history(user: Optional[Dict[str, Any]] = Depends(get_user_from_header)):
    if not user:
        raise HTTPException(status_code=401, detail="Please log in to clear history.")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM history WHERE user_id = ?;", (user["id"],))
    conn.commit()
    conn.close()
    return {"success": True, "message": "History cleared successfully."}


@app.post("/api/user/bookmarks")
def add_bookmark(req: BookmarkRequest, user: Optional[Dict[str, Any]] = Depends(get_user_from_header)):
    if not user:
        raise HTTPException(status_code=401, detail="Please log in to bookmark poems.")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO bookmarks (user_id, verse_id, work, verse_number)
            VALUES (?, ?, ?, ?);
        """, (user["id"], req.verse_id, req.work, str(req.verse_number)))
        conn.commit()
    finally:
        conn.close()
    return {"success": True, "message": "Bookmarked successfully."}


@app.get("/api/user/bookmarks")
def get_bookmarks(user: Optional[Dict[str, Any]] = Depends(get_user_from_header)):
    if not user:
        raise HTTPException(status_code=401, detail="Please log in to view bookmarks.")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.id, b.verse_id, b.work, b.verse_number, b.created_at,
               c.text_tamil, c.explanation_tamil, c.explanation_english, c.chapter_name
        FROM bookmarks b
        LEFT JOIN literature_corpus c ON b.verse_id = c.id
        WHERE b.user_id = ?
        ORDER BY b.created_at DESC;
    """, (user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return {"bookmarks": [dict(r) for r in rows]}


@app.delete("/api/user/bookmarks/{verse_id}")
def remove_bookmark(verse_id: str, user: Optional[Dict[str, Any]] = Depends(get_user_from_header)):
    if not user:
        raise HTTPException(status_code=401, detail="Please log in.")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bookmarks WHERE user_id = ? AND verse_id = ?;", (user["id"], verse_id))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Bookmark removed."}


# =====================================================================
# 7. SYSTEM MONITORING & HEALTH
# =====================================================================
@app.get("/health")
def health_check():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM literature_corpus;")
    count = cursor.fetchone()[0]
    conn.close()
    return {
        "status": "healthy",
        "database_ready": True,
        "total_canonical_records": count,
        "database_path": str(DB_PATH)
    }


# Mount static assets if available
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
