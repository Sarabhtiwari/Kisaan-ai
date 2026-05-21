from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    session_id: str
    message: str
    language: str = "hi"
    image_base64: Optional[str] = None
    location: Optional[dict] = None

class ChatResponse(BaseModel):
    reply: str
    tool_used: Optional[str] = None
    session_id: str