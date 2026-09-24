"""
auth.py
-------
Authentication and session management for Tamil Ilakkiya AI.
Provides real email/password signup, login, session tokens, and password reset.
All credentials and sessions are securely stored in the persistent SQLite database.
"""

import os
import secrets
import hashlib
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "literature.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Secure PBKDF2-HMAC-SHA256 password hashing with random salt."""
    if not salt:
        salt = secrets.token_hex(16)
    pw_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return f"{salt}:{pw_hash}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verifies a password against the stored salt:hash string."""
    try:
        salt, pw_hash = stored_hash.split(':')
        computed = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        return secrets.compare_digest(pw_hash, computed)
    except Exception:
        return False


def register_user(email: str, password: str, name: Optional[str] = None) -> Dict[str, Any]:
    """Registers a new user and generates an authenticated session token."""
    email_clean = email.strip().lower()
    if not email_clean or '@' not in email_clean:
        return {"success": False, "message": "Invalid email address / தவறான மின்னஞ்சல் முகவரி."}
    if len(password) < 6:
        return {"success": False, "message": "Password must be at least 6 characters / கடவுச்சொல் குறைந்தபட்சம் 6 எழுத்துக்கள் இருக்க வேண்டும்."}

    display_name = name.strip() if name and name.strip() else email_clean.split('@')[0]
    p_hash = hash_password(password)

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?);",
            (email_clean, p_hash, display_name)
        )
        user_id = cursor.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return {"success": False, "message": "This email is already registered / இந்த மின்னஞ்சல் ஏற்கனவே பதிவு செய்யப்பட்டுள்ளது."}

    # Generate session token (valid 30 days)
    token = secrets.token_urlsafe(32)
    expires = (datetime.utcnow() + timedelta(days=30)).isoformat()
    cursor.execute(
        "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?);",
        (token, user_id, expires)
    )
    conn.commit()
    conn.close()

    return {
        "success": True,
        "token": token,
        "user": {
            "id": user_id,
            "email": email_clean,
            "name": display_name
        }
    }


def login_user(email: str, password: str) -> Dict[str, Any]:
    """Validates user credentials and issues a session token."""
    email_clean = email.strip().lower()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, email, password_hash, name FROM users WHERE email = ?;", (email_clean,))
    user = cursor.fetchone()
    if not user or not verify_password(password, user["password_hash"]):
        conn.close()
        return {"success": False, "message": "Invalid email or password / தவறான மின்னஞ்சல் அல்லது கடவுச்சொல்."}

    token = secrets.token_urlsafe(32)
    expires = (datetime.utcnow() + timedelta(days=30)).isoformat()
    cursor.execute(
        "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?);",
        (token, user["id"], expires)
    )
    conn.commit()
    conn.close()

    return {
        "success": True,
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"]
        }
    }


def reset_password(email: str, new_password: str) -> Dict[str, Any]:
    """Resets user password."""
    email_clean = email.strip().lower()
    if len(new_password) < 6:
        return {"success": False, "message": "New password must be at least 6 characters."}

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?;", (email_clean,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return {"success": False, "message": "Account not found with this email / இந்த மின்னஞ்சலில் கணக்கு காணப்படவில்லை."}

    new_hash = hash_password(new_password)
    cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?;", (new_hash, user["id"]))
    # Invalidate old sessions
    cursor.execute("DELETE FROM sessions WHERE user_id = ?;", (user["id"],))
    conn.commit()
    conn.close()

    return {"success": True, "message": "Password reset successfully / கடவுச்சொல் வெற்றிகரமாக மாற்றப்பட்டது."}


def get_current_user(token: Optional[str]) -> Optional[Dict[str, Any]]:
    """Retrieves authenticated user from SQLite session token."""
    if not token:
        return None

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.email, u.name, s.expires_at
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.token = ?;
    """, (token.strip(),))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    try:
        exp = datetime.fromisoformat(row["expires_at"])
        if exp < datetime.utcnow():
            return None
    except Exception:
        pass

    return {
        "id": row["id"],
        "email": row["email"],
        "name": row["name"]
    }
