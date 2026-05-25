# short_term.py
# Upgraded memory with summarization
# When history gets long, older messages get summarized
# So AI never forgets important context from early conversation

from typing import List
from app.config import GROQ_API_KEY
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.3-70b-versatile",
    temperature=0
)

# Storage: session_id -> {"messages": [...], "summary": "..."}
conversation_store = {}

SUMMARY_PROMPT = """Summarize this farming conversation in 2-3 sentences.
Focus on: farmer's name, location, crops they grow, problems they mentioned.
Be concise. This summary will be used as context for future messages.

Conversation:
{conversation}

Summary:"""

def _summarize(messages: List[dict]) -> str:
    """Summarize a list of messages into one paragraph."""
    conversation_text = ""
    for msg in messages:
        role = "Farmer" if msg["role"] == "user" else "AI"
        conversation_text += f"{role}: {msg['content']}\n"

    response = llm.invoke([
        SystemMessage(content="You are a helpful assistant that summarizes conversations."),
        HumanMessage(content=SUMMARY_PROMPT.format(conversation=conversation_text))
    ])
    return response.content.strip()

def get_history(session_id: str) -> List[dict]:
    """
    Returns history for this session.
    Format: [{"role": "system", "content": "Summary: ..."}, ...last 4 messages]
    """
    if session_id not in conversation_store:
        return []

    data = conversation_store[session_id]
    summary = data.get("summary", "")
    messages = data.get("messages", [])

    result = []

    # Add summary as first item if exists
    if summary:
        result.append({
            "role": "system",
            "content": f"Conversation summary so far: {summary}"
        })

    # Add last 4 full messages
    result.extend(messages[-4:])
    return result

def save_message(session_id: str, role: str, content: str):
    """
    Save message. If messages exceed 8, summarize older ones.
    """
    if session_id not in conversation_store:
        conversation_store[session_id] = {"messages": [], "summary": ""}

    conversation_store[session_id]["messages"].append({
        "role": role,
        "content": content
    })

    messages = conversation_store[session_id]["messages"]

    # When we have more than 8 messages, summarize the older ones
    if len(messages) > 8:
        # Take all except last 4
        to_summarize = messages[:-4]
        last_4 = messages[-4:]

        # Generate new summary
        existing_summary = conversation_store[session_id].get("summary", "")
        
        if existing_summary:
            # Include existing summary in new summarization
            summary_input = [{"role": "system", "content": existing_summary}] + to_summarize
        else:
            summary_input = to_summarize

        new_summary = _summarize(summary_input)

        # Keep only last 4 messages, store summary separately
        conversation_store[session_id]["summary"] = new_summary
        conversation_store[session_id]["messages"] = last_4

        print(f"Memory summarized for session {session_id}: {new_summary[:100]}...")