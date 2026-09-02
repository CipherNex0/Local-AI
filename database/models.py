"""
Data-access layer for conversations and messages.

Every function here is a single, focused SQL operation. No
auto-titling, no AI calls, no request/response shaping — that
orchestration belongs in services/conversation_service.py. This file
should stay boring and easy to verify against the schema in db.py.
"""

import uuid
from datetime import datetime, timezone

from database.db import get_db


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- conversations ----------------------------------------------------

def create_conversation(visitor_id: str, title: str = "New conversation") -> dict:
    convo_id = str(uuid.uuid4())
    now = _now()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO conversations (id, visitor_id, title, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (convo_id, visitor_id, title, now, now),
        )
    return {"id": convo_id, "visitor_id": visitor_id, "title": title, "created_at": now, "updated_at": now}


def list_conversations(visitor_id: str) -> list[dict]:
    """Every conversation, newest first, with a one-line preview."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, title, updated_at FROM conversations "
            "WHERE visitor_id = ?"
            "ORDER BY updated_at DESC",
            (visitor_id,)
        ).fetchall()

        result = []
        for row in rows:
            last = conn.execute(
                "SELECT content FROM messages WHERE conversation_id = ? "
                "ORDER BY id DESC LIMIT 1",
                (row["id"],),
            ).fetchone()
            result.append({
                "id": row["id"],
                "title": row["title"],
                "updated_at": row["updated_at"],
                "preview": last["content"] if last else "No messages yet",
            })
        return result


def get_conversation(convo_id: str, visitor_id: str) -> dict | None:
    with get_db() as conn:
        convo = conn.execute(
            "SELECT * FROM conversations WHERE id = ? AND visitor_id = ?", (convo_id, visitor_id)
        ).fetchone()
        
        if not convo:
            return None

        messages = conn.execute(
            "SELECT role, content, attachment, attachment_path, created_at "
            "FROM messages WHERE conversation_id = ? ORDER BY id ASC",
            (convo_id,)
        ).fetchall()

        return {
            "id": convo["id"],
            "visitor_id": convo["visitor_id"],
            "title": convo["title"],
            "messages": [dict(m) for m in messages],
        }


def rename_conversation(convo_id: str, title: str) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
            (title, _now(), convo_id),
        )


def touch_conversation(convo_id: str) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (_now(), convo_id),
        )


def delete_conversation(convo_id: str) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM conversations WHERE id = ?", (convo_id,))


def delete_all_conversations() -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM conversations")


def clear_messages(convo_id: str) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM messages WHERE conversation_id = ?", (convo_id,))


# --- messages -------------------------------------------------------------

def add_message(
    convo_id: str,
    role: str,
    content: str,
    attachment: str | None = None,
    attachment_path: str | None = None,
) -> None:
    with get_db() as conn:
        conn.execute(
            "INSERT INTO messages "
            "(conversation_id, role, content, attachment, attachment_path, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (convo_id, role, content, attachment, attachment_path, _now()),
        )
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (_now(), convo_id),
        )


# --- export -----------------------------------------------------------

def export_conversation_text(convo_id: str) -> str | None:
    convo = get_conversation(convo_id)
    if not convo:
        return None
    lines = [f"# {convo['title']}", ""]
    for m in convo["messages"]:
        speaker = "You" if m["role"] == "user" else "Zora"
        lines.append(f"{speaker}: {m['content']}")
        if m["attachment"]:
            lines.append(f"  (attached: {m['attachment']})")
        lines.append("")
    return "\n".join(lines)


def export_all() -> list[dict]:
    with get_db() as conn:
        convos = conn.execute(
            "SELECT id, title, created_at, updated_at FROM conversations "
            "ORDER BY updated_at DESC"
        ).fetchall()

        data = []
        for c in convos:
            messages = conn.execute(
                "SELECT role, content, attachment, attachment_path, created_at "
                "FROM messages WHERE conversation_id = ? ORDER BY id ASC",
                (c["id"],),
            ).fetchall()
            data.append({**dict(c), "messages": [dict(m) for m in messages]})
        return data