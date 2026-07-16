"""
TCF Discovery Agent — Database Layer
Stores every submission using SQLite (file-based, no server setup needed).

Developed by Qarib Javed
"""

import sqlite3
import json
import os
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "discovery_agent.db")


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Creates the submissions table if it doesn't already exist. Safe to call every startup."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                riasec_scores TEXT NOT NULL,
                big_five_scores TEXT NOT NULL,
                skills_ratings TEXT NOT NULL,
                contradiction_flags TEXT NOT NULL,
                suggested_fields TEXT NOT NULL,
                valid_response INTEGER NOT NULL,
                student_report TEXT NOT NULL,
                counsellor_report TEXT NOT NULL
            )
        """)


def save_submission(student_name: str, skills_ratings: dict, result: dict) -> int:
    """Saves one completed assessment. Returns the new row's id."""
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO submissions (
                student_name, created_at, riasec_scores, big_five_scores,
                skills_ratings, contradiction_flags, suggested_fields,
                valid_response, student_report, counsellor_report
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            student_name,
            datetime.utcnow().isoformat(),
            json.dumps(result.get("riasec_scores", {})),
            json.dumps(result.get("big_five_scores", {})),
            json.dumps(skills_ratings),
            json.dumps(result.get("contradiction_flags", [])),
            json.dumps(result.get("suggested_fields", [])),
            1 if result.get("valid_response", True) else 0,
            result.get("student_report", ""),
            result.get("counsellor_report", ""),
        ))
        return cursor.lastrowid


def get_all_submissions() -> list:
    """Returns all submissions, most recent first (summary fields only, for the list view)."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, student_name, created_at, suggested_fields, valid_response
            FROM submissions ORDER BY created_at DESC
        """).fetchall()
        return [
            {
                "id": r["id"],
                "student_name": r["student_name"],
                "created_at": r["created_at"],
                "suggested_fields": json.loads(r["suggested_fields"]),
                "valid_response": bool(r["valid_response"]),
            }
            for r in rows
        ]


def get_submission_by_id(submission_id: int):
    """Returns the full record for one submission, or None if not found."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,)).fetchone()
        if row is None:
            return None
        return {
            "id": row["id"],
            "student_name": row["student_name"],
            "created_at": row["created_at"],
            "riasec_scores": json.loads(row["riasec_scores"]),
            "big_five_scores": json.loads(row["big_five_scores"]),
            "skills_ratings": json.loads(row["skills_ratings"]),
            "contradiction_flags": json.loads(row["contradiction_flags"]),
            "suggested_fields": json.loads(row["suggested_fields"]),
            "valid_response": bool(row["valid_response"]),
            "student_report": row["student_report"],
            "counsellor_report": row["counsellor_report"],
        }
