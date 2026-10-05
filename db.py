import os
import sqlite3
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "tickets.db")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _connect()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source TEXT NOT NULL,
            text TEXT NOT NULL,
            category TEXT,
            priority TEXT,
            angry INTEGER,
            confidence REAL,
            status TEXT,
            reasons TEXT,
            answer TEXT,
            answer_source TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def save_ticket(text, result, source="web"):
    conn = _connect()
    cur = conn.execute(
        """
        INSERT INTO tickets
        (created_at, source, text, category, priority, angry, confidence,
         status, reasons, answer, answer_source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            source,
            text,
            result["category"],
            result["priority"],
            1 if result["angry"] else 0,
            result["confidence"],
            result["status"],
            "; ".join(result["reasons"]),
            result["answer"],
            result["source"],
        ),
    )
    conn.commit()
    ticket_id = cur.lastrowid
    conn.close()
    return ticket_id


def list_tickets(limit=50):
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM tickets ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats():
    conn = _connect()
    total = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
    auto = conn.execute(
        "SELECT COUNT(*) FROM tickets WHERE status = 'auto_answered'"
    ).fetchone()[0]
    by_category = {
        r[0]: r[1]
        for r in conn.execute(
            "SELECT category, COUNT(*) FROM tickets GROUP BY category"
        )
    }
    by_priority = {
        r[0]: r[1]
        for r in conn.execute(
            "SELECT priority, COUNT(*) FROM tickets GROUP BY priority"
        )
    }
    conn.close()
    return {
        "total": total,
        "auto_answered": auto,
        "escalated": total - auto,
        "auto_rate": round(100 * auto / total, 1) if total else 0,
        "by_category": by_category,
        "by_priority": by_priority,
    }