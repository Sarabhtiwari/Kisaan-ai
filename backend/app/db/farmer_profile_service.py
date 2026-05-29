# farmer_profile_service.py
# Handles all reading and writing to farmer_profiles table
# Creates profile on first visit, updates on subsequent visits

from app.db.supabase import client

def get_or_create_profile(session_id: str, language: str = "hi") -> dict:
    """
    Get existing profile or create new one.
    Returns profile dict.
    """
    try:
        # Try to find existing profile
        response = client.table("farmer_profiles")\
            .select("*")\
            .eq("session_id", session_id)\
            .execute()

        if response.data:
            return response.data[0]

        # Profile not found — create new one
        new_profile = {
            "session_id": session_id,
            "language":   language,
        }

        response = client.table("farmer_profiles")\
            .insert(new_profile)\
            .execute()

        return response.data[0] if response.data else new_profile

    except Exception as e:
        print(f"Error getting profile: {e}")
        return {"session_id": session_id, "language": language}


def update_profile(session_id: str, updates: dict):
    """
    Update specific fields in farmer profile.
    Only updates fields that are provided.
    
    Example:
    update_profile("farmer_abc", {"name": "Ramesh", "location": "Lucknow"})
    """
    try:
        if not updates:
            return

        # Add updated_at timestamp
        updates["updated_at"] = "NOW()"

        client.table("farmer_profiles")\
            .update(updates)\
            .eq("session_id", session_id)\
            .execute()

    except Exception as e:
        print(f"Error updating profile: {e}")


def update_summary(session_id: str, summary: str):
    """Save conversation summary to profile."""
    try:
        client.table("farmer_profiles")\
            .update({"summary": summary})\
            .eq("session_id", session_id)\
            .execute()
    except Exception as e:
        print(f"Error updating summary: {e}")


def get_summary(session_id: str) -> str:
    """Get conversation summary for this farmer."""
    try:
        response = client.table("farmer_profiles")\
            .select("summary")\
            .eq("session_id", session_id)\
            .execute()

        if response.data and response.data[0].get("summary"):
            return response.data[0]["summary"]
        return ""

    except Exception as e:
        print(f"Error getting summary: {e}")
        return ""