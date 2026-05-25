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

# Streaming LLM instance — only used for final response
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

    # Step 2 — Run agent (supervisor + tool only, not synthesizer)
    result = agent.invoke({
        "session_id":   request.session_id,
        "message":      request.message,
        "language":     request.language,
        "image_base64": request.image_base64,
        "location":     request.location or {"city": "Lucknow"},
        "chat_history": history,
        "tool_to_use":  None,
        "tool_result":  None,
        "final_reply":  None,
    })

    # Step 3 — Format history for prompt
    history_text = "No previous conversation."
    if history:
        lines = []
        for msg in history[-6:]:
            role = "Farmer" if msg["role"] == "user" else "AI"
            lines.append(f"{role}: {msg['content']}")
        history_text = "\n".join(lines)

    # Step 4 — Build synthesizer prompt
    prompt = SYNTHESIZER_PROMPT.format(
        history=history_text,
        message=request.message,
        tool_used=result.get("tool_to_use", "general"),
        tool_result=result.get("tool_result", "No data available")
    )

    # Step 5 — Stream function
    # This runs after agent finishes
    # Sends chunks one by one to frontend
    async def generate():
        full_reply = ""
        tool_used = result.get("tool_to_use", "general")

        # First chunk — tell frontend which tool was used
        yield f"data: {json.dumps({'type': 'tool', 'tool': tool_used})}\n\n"

        # Stream synthesizer word by word
        async for chunk in llm.astream([
            SystemMessage(content=prompt),
            HumanMessage(content="Generate the farmer friendly response now.")
        ]):
            if chunk.content:
                full_reply += chunk.content
                # Send each word/piece to frontend
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk.content})}\n\n"

        # Tell frontend streaming is done
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

        # Save complete conversation to memory
        save_message(request.session_id, "user", request.message)
        save_message(request.session_id, "assistant", full_reply)

    # Return streaming response
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )