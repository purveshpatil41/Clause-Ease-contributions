import sqlite3
from datetime import datetime

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b-instruct"
DB_PATH = "users.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_documents_db():
    conn = get_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS documents(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT,
            mime TEXT,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    conn.commit()
    conn.close()


def list_documents(user_id):
    init_documents_db()
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, filename, mime, content, created_at FROM documents WHERE user_id=? ORDER BY id DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return rows


def save_document(user_id, content, filename=None, mime="text/plain"):
    init_documents_db()
    conn = get_conn()
    conn.execute(
        "INSERT INTO documents(user_id, filename, mime, content, created_at) VALUES(?,?,?,?,?)",
        (user_id, filename, mime, content, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def summarize_text(text, compression_ratio=0.4):
    """
    Summarize text with the local Qwen model through Ollama.
    compression_ratio controls how short or detailed the summary should be.
    """
    word_count = len(text.split())
    target_words = max(30, int(word_count * compression_ratio))

    prompt = f"""
You are a legal document summarizer.

Summarize the following text in clear plain English.
Do not copy long sentences from the original text.
Keep the important obligations, dates, parties, risks, and conditions.
Do not add legal advice.
Aim for about {target_words} words.

Text:
{text}

Summary:
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": max(80, target_words * 2),
            },
        },
        timeout=180
    )

    response.raise_for_status()
    data = response.json()

    return data["response"].strip()

def simplify_text(text, level="Intermediate"):
    prompt = f"""
You are a legal text simplifier.

Rewrite the following legal text in simple plain English.
Keep the original meaning.
Replace legal terms with common words when possible.
Do not add legal advice.
Do not skip important obligations.

Legal text:
{text}

Simplified version:
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        },
        timeout=120
    )

    response.raise_for_status()
    data = response.json()

    return data["response"].strip()
