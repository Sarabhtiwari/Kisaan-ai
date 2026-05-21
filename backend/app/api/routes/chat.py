from fastapi import APIRouter
from app.models.schemas import ChatRequest, ChatResponse
from app.agent.graph import agent

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    
    result = agent.invoke({
        "session_id":   request.session_id,
        "message":      request.message,
        "language":     request.language,
        "image_base64": request.image_base64,
        "location":     request.location or {"city": "Lucknow"},
        "tool_to_use":  None,
        "tool_result":  None,
        "final_reply":  None,
    })

    return ChatResponse(
        reply=result["final_reply"] or "माफ करें, कुछ गड़बड़ हो गई।",
        tool_used=result.get("tool_to_use"),
        session_id=request.session_id
    )