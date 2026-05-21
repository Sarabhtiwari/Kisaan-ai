from typing import TypedDict, Optional

class AgentState(TypedDict):
    session_id:    str
    message:       str
    language:      str
    image_base64:  Optional[str]
    location:      Optional[dict]
    tool_to_use:   Optional[str]
    tool_result:   Optional[str]
    final_reply:   Optional[str]