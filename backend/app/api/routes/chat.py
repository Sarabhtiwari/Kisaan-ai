from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatRequest
from app.agent.graph import agent
from app.db.conversation_service import save_message, get_last_messages
from app.db.farmer_profile_service import get_or_create_profile, update_summary
from app.memory.short_term import get_history as get_short_term
from app.config import GROQ_API_KEY
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
import json

router = APIRouter()

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.3-70b-versatile",
    temperature=0.4,
    streaming=True
)

SYNTHESIZER_PROMPT = """You are Kisaan AI, a friendly farming assistant for Indian farmers.

Convert the raw tool data into a warm helpful reply.

Rules:
- Reply in the same language the farmer used
- Use simple words, no jargon
- Be warm and respectful
- Give concrete actionable advice
- Keep reply under 120 words
- If farmer told you their name earlier, use it
- If farmer mentioned crop or location earlier, refer to it

Farmer profile:
{profile}

Conversation history:
{history}

Farmer's current question: {message}
Tool used: {tool_used}
Raw data: {tool_result}"""


@router.post("/chat")
async def chat(request: ChatRequest):

    # Step 1 — Get farmer profile from Supabase
    profile = get_or_create_profile(request.session_id, request.language)

    # Step 2 — Load conversation history from Supabase
    history = get_last_messages(request.session_id, limit=10)

    # Step 3 — If no Supabase history, fall back to short term memory
    if not history:
        history = get_short_term(request.session_id)

    # Step 4 — Run agent
    result = agent.invoke({
        "session_id":   request.session_id,
        "message":      request.message,
        "language":     request.language,
        "image_base64": request.image_base64,
        "location":     request.location or {"city": profile.get("location", "Lucknow")},
        "chat_history": history,
        "tool_to_use":  None,
        "tools_to_use": [],
        "tool_result":  None,
        "tool_results": [],
        "final_reply":  None,
    })

    # Step 5 — Prepare synthesizer inputs
    tool_results = result.get("tool_results", [])
    combined_result = "\n\n".join(tool_results) if tool_results else result.get("tool_result") or "No data available"
    tools_used = ", ".join(result.get("tools_to_use") or [result.get("tool_to_use") or "general"])

    # Step 6 — Format history for prompt
    history_text = "No previous conversation."
    if history:
        lines = []
        for msg in history[-6:]:
            role = "Farmer" if msg["role"] == "user" else "AI"
            lines.append(f"{role}: {msg['content']}")
        history_text = "\n".join(lines)

    # Step 7 — Format profile for prompt
    profile_text = ""
    if profile.get("name"):
        profile_text += f"Name: {profile['name']}\n"
    if profile.get("location"):
        profile_text += f"Location: {profile['location']}\n"
    if profile.get("crops"):
        profile_text += f"Crops: {profile['crops']}\n"
    if profile.get("summary"):
        profile_text += f"Previous summary: {profile['summary']}\n"
    if not profile_text:
        profile_text = "New farmer, no profile yet."

    # Step 8 — Build final prompt
    final_prompt = SYNTHESIZER_PROMPT.format(
        profile=profile_text,
        history=history_text,
        message=request.message,
        tool_used=tools_used,
        tool_result=combined_result
    )

    # Step 9 — Stream response
    async def generate():
        full_reply = ""

        yield f"data: {json.dumps({'type': 'tool', 'tool': tools_used})}\n\n"

        async for chunk in llm.astream([
            SystemMessage(content=final_prompt),
            HumanMessage(content="Generate the farmer friendly response now.")
        ]):
            if chunk.content:
                full_reply += chunk.content
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk.content})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

        # Save to Supabase after streaming
        save_message(request.session_id, "user", request.message, None)
        save_message(request.session_id, "assistant", full_reply, tools_used)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )