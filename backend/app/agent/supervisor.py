from app.agent.state import AgentState
from app.config import GROQ_API_KEY
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.3-70b-versatile",
    temperature=0
)

SUPERVISOR_PROMPT = """You are a routing assistant. Read the farmer's message and reply with ONLY one word:

- disease     → crop disease, pest, yellowing, spots, insects, damage, photo
- weather     → rain, weather, temperature, irrigation timing
- mandi       → price, rate, mandi, market, sell, crop value
- schemes     → government scheme, subsidy, loan, PM Kisan, registration
- general     → everything else

Reply with ONLY that one word. Nothing else."""

def supervisor_node(state: AgentState) -> AgentState:
    # Build context from last 4 messages
    history_text = ""
    if state.get("chat_history"):
        history_text = "\nPrevious conversation:\n"
        for msg in state["chat_history"][-4:]:
            role = "Farmer" if msg["role"] == "user" else "AI"
            history_text += f"{role}: {msg['content']}\n"

    full_message = f"{history_text}\nCurrent message: {state['message']}"

    response = llm.invoke([
        SystemMessage(content=SUPERVISOR_PROMPT),
        HumanMessage(content=full_message)
    ])

    decision = response.content.strip().lower()
    valid = {"disease", "weather", "mandi", "schemes", "general"}
    if decision not in valid:
        decision = "general"

    state["tool_to_use"] = decision
    return state