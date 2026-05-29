# Handles all reading and writing to conversations table
# Every message sent and received is saved here permanently

from app.db.supabase import client
from typing import List

def save_message(session_id: str, role: str, content: str, tool_used: str = None):
    """Save one message to conversations table."""
    try:
        client.table("conversations").insert({
            "session_id": session_id,
            "role":       role,
            "content":    content,
            "tool_used":  tool_used
        }).execute()
    except Exception as e:
        print(f"Error saving message: {e}")

def get_last_messages(session_id: str, limit: int = 10) -> List[dict]:
    """
    Get last N messages for this session.
    Returns in chronological order (oldest first).
    """
    try:
        response = client.table("conversations")\
            .select("role, content")\
            .eq("session_id", session_id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()

        messages = response.data or []

        # Reverse so oldest message is first
        messages.reverse()

        # Format same as short_term.py
        return [
            {
                "role": msg["role"],
                "content": msg["content"]
            }
            for msg in messages
        ]

    except Exception as e:
        print(f"Error loading messages: {e}")
        return []