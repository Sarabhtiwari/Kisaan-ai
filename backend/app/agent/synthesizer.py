from app.agent.state import AgentState
from app.config import GROQ_API_KEY
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.3-70b-versatile",
    temperature=0.4
)

SYNTHESIZER_PROMPT = """You are Kisaan AI, a friendly farming assistant for Indian farmers.

Convert the raw tool data into a warm helpful reply.

Rules:
- Reply in the same language the farmer used
- Use simple words
- Be warm and respectful
- Give concrete actionable advice
- Keep reply under 120 words
- If farmer told you their name earlier in history, use it
- If farmer mentioned their crop or location earlier, refer to it

Conversation history:
{history}

Farmer's current question: {message}
Tool used: {tool_used}
Raw data: {tool_result}"""

def synthesizer_node(state: AgentState) -> AgentState:
    # Format history for prompt
    history_text = "No previous conversation."
    if state.get("chat_history"):
        lines = []
        for msg in state["chat_history"][-6:]:
            role = "Farmer" if msg["role"] == "user" else "AI"
            lines.append(f"{role}: {msg['content']}")
        history_text = "\n".join(lines)

    prompt = SYNTHESIZER_PROMPT.format(
        history=history_text,
        message=state["message"],
        tool_used=state.get("tool_to_use", "general"),
        tool_result=state.get("tool_result", "No data available")
    )

    response = llm.invoke([
        SystemMessage(content=prompt),
        HumanMessage(content="Generate the farmer friendly response now.")
    ])

    state["final_reply"] = response.content.strip()
    return state