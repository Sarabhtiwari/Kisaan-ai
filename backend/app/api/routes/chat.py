from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatRequest
from app.agent.graph import agent
from app.memory.short_term import get_history, save_message
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

Conversation history:
{history}

Farmer's current question: {message}
Tool used: {tool_used}
Raw data: {tool_result}"""


@router.post("/chat")
async def chat(request: ChatRequest):

    # Step 1 — Load memory
    history = get_history(request.session_id)

    # Step 2 — Run agent
    result = agent.invoke({
        "session_id":   request.session_id,
        "message":      request.message,
        "language":     request.language,
        "image_base64": request.image_base64,
        "location":     request.location or {"city": "Lucknow"},
        "chat_history": history,
        "tool_to_use":  None,
        "tools_to_use": [],
        "tool_result":  None,
        "tool_results": [],
        "final_reply":  None,
    })

    # Step 3 — Capture all result data before streaming
    tool_results = result.get("tool_results", [])
    combined_result = "\n\n".join(tool_results) if tool_results else result.get("tool_result") or "No data available"
    tools_used = ", ".join(result.get("tools_to_use") or [result.get("tool_to_use") or "general"])

    # Step 4 — Format history
    history_text = "No previous conversation."
    if history:
        lines = []
        for msg in history[-6:]:
            role = "Farmer" if msg["role"] == "user" else "AI"
            lines.append(f"{role}: {msg['content']}")
        history_text = "\n".join(lines)

    # Step 5 — Build prompt here, before generate()
    # This way generate() can access it via closure
    final_prompt = SYNTHESIZER_PROMPT.format(
        history=history_text,
        message=request.message,
        tool_used=tools_used,
        tool_result=combined_result
    )

    # Step 6 — Stream function
    async def generate():
        full_reply = ""

        # Send tool name first
        yield f"data: {json.dumps({'type': 'tool', 'tool': tools_used})}\n\n"

        # Stream synthesizer word by word
        async for chunk in llm.astream([
            SystemMessage(content=final_prompt),
            HumanMessage(content="Generate the farmer friendly response now.")
        ]):
            if chunk.content:
                full_reply += chunk.content
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk.content})}\n\n"

        # Done signal
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

        # Save to memory
        save_message(request.session_id, "user", request.message)
        save_message(request.session_id, "assistant", full_reply)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )