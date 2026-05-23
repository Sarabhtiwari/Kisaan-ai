from typing import List

# Main storage — dictionary of session_id -> message list
# Example:
# {
#   "farmer_abc123": [
#     {"role": "user", "content": "mera naam Ramesh hai"},
#     {"role": "assistant", "content": "Namaste Ramesh ji..."}
#   ]
# }
conversation_store = {}

def get_history(session_id: str) -> List[dict]:
    """Get last 10 messages for this session."""
    history = conversation_store.get(session_id, [])
    return history[-10:]  # only last 10 to avoid token overflow

def save_message(session_id: str, role: str, content: str):
    """Save one message to this session's history."""
    if session_id not in conversation_store:
        conversation_store[session_id] = []
    
    conversation_store[session_id].append({
        "role": role,
        "content": content
    })