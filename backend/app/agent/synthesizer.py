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

You will receive raw data from a tool. Convert it into a warm, helpful reply.

Rules:
- Reply in the same language the farmer used
- Use simple words, no technical jargon
- Be warm and respectful
- Give concrete actionable advice
- Keep reply under 120 words

Farmer's question: {message}
Tool used: {tool_used}
Raw data: {tool_result}"""

def synthesizer_node(state: AgentState) -> AgentState:
    prompt = SYNTHESIZER_PROMPT.format(
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