from app.agent.state import AgentState
from app.config import GROQ_API_KEY
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.3-70b-versatile",
    temperature=0
)

SUPERVISOR_PROMPT = """You are a routing assistant. Read the farmer's message and reply with ONLY one word from this list:

- disease     → farmer mentions crop disease, pest, yellowing, spots, insects, damage, or sends a photo
- weather     → farmer asks about rain, weather, temperature, irrigation timing
- mandi       → farmer asks about price, rate, mandi, market, sell, crop value
- schemes     → farmer asks about government scheme, subsidy, loan, PM Kisan, registration
- general     → everything else

Reply with ONLY that one word. No explanation. No punctuation. Just the word."""

def supervisor_node(state: AgentState) -> AgentState:
    response = llm.invoke([
        SystemMessage(content=SUPERVISOR_PROMPT),
        HumanMessage(content=state["message"])
    ])

    decision = response.content.strip().lower()

    valid = {"disease", "weather", "mandi", "schemes", "general"}
    if decision not in valid:
        decision = "general"

    state["tool_to_use"] = decision
    return state