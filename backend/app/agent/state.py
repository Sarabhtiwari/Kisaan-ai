from typing import TypedDict, Optional, List, Annotated
import operator

def keep_last(a, b):
    return b if b is not None else a

class AgentState(TypedDict):
    # Read-only fields — same value across all parallel nodes
    session_id:    Annotated[str, keep_last]
    message:       Annotated[str, keep_last]
    language:      Annotated[str, keep_last]
    image_base64:  Annotated[Optional[str], keep_last]
    location:      Annotated[Optional[dict], keep_last]
    chat_history:  Annotated[List[dict], keep_last]
    tool_to_use:   Annotated[Optional[str], keep_last]
    tools_to_use:  Annotated[List[str], keep_last]
    final_reply:   Annotated[Optional[str], keep_last]

    # tool_result kept for single tool compatibility
    tool_result:   Annotated[Optional[str], keep_last]

    # tool_results collects ALL parallel results
    # operator.add appends each node's result to the list
    tool_results:  Annotated[List[str], operator.add]