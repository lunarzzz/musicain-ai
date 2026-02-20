"""SQLite 对话持久化"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "musician_ai.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """创建表结构"""
    conn = _get_conn()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS conversation (
            id          TEXT PRIMARY KEY,
            title       TEXT NOT NULL DEFAULT '新对话',
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS message (
            id              TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            role            TEXT NOT NULL,
            content         TEXT NOT NULL DEFAULT '',
            tool_calls      TEXT,
            cards           TEXT,
            evidence        TEXT,
            created_at      TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversation(id)
        );

        CREATE INDEX IF NOT EXISTS idx_msg_conv ON message(conversation_id);
        """
    )
    conn.commit()
    conn.close()


# ── 会话 ──────────────────────────────────────────────

def create_conversation(title: str = "新对话") -> str:
    conv_id = uuid.uuid4().hex[:16]
    now = datetime.now().isoformat()
    conn = _get_conn()
    conn.execute(
        "INSERT INTO conversation (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (conv_id, title, now, now),
    )
    conn.commit()
    conn.close()
    return conv_id


def update_conversation_title(conv_id: str, title: str) -> None:
    conn = _get_conn()
    conn.execute(
        "UPDATE conversation SET title = ?, updated_at = ? WHERE id = ?",
        (title, datetime.now().isoformat(), conv_id),
    )
    conn.commit()
    conn.close()


def list_conversations(limit: int = 50) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        """
        SELECT c.id, c.title, c.updated_at,
               COUNT(m.id) as message_count
        FROM conversation c
        LEFT JOIN message m ON m.conversation_id = c.id
        GROUP BY c.id
        ORDER BY c.updated_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_conversation(conv_id: str) -> dict | None:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM conversation WHERE id = ?", (conv_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_conversation(conv_id: str) -> None:
    conn = _get_conn()
    conn.execute("DELETE FROM message WHERE conversation_id = ?", (conv_id,))
    conn.execute("DELETE FROM conversation WHERE id = ?", (conv_id,))
    conn.commit()
    conn.close()


# ── 消息 ──────────────────────────────────────────────

def save_message(
    conversation_id: str,
    role: str,
    content: str,
    tool_calls: list | None = None,
    cards: list | None = None,
    evidence: list | None = None,
) -> str:
    msg_id = uuid.uuid4().hex[:16]
    now = datetime.now().isoformat()
    conn = _get_conn()
    conn.execute(
        """INSERT INTO message
           (id, conversation_id, role, content, tool_calls, cards, evidence, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            msg_id,
            conversation_id,
            role,
            content,
            json.dumps(tool_calls) if tool_calls else None,
            json.dumps(cards) if cards else None,
            json.dumps(evidence) if evidence else None,
            now,
        ),
    )
    conn.execute(
        "UPDATE conversation SET updated_at = ? WHERE id = ?",
        (now, conversation_id),
    )
    conn.commit()
    conn.close()
    return msg_id


def get_messages(conversation_id: str, limit: int = 50) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        """SELECT * FROM message
           WHERE conversation_id = ?
           ORDER BY created_at ASC
           LIMIT ?""",
        (conversation_id, limit),
    ).fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        for field in ("tool_calls", "cards", "evidence"):
            if d.get(field):
                d[field] = json.loads(d[field])
        results.append(d)
    return results
