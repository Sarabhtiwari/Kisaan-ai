from app.agent.state import AgentState
from app.config import GROQ_API_KEY
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.3-70b-versatile",
    temperature=0
)

# Keywords that force specific tools - no LLM needed
FORCED_ROUTING = {
    "web_search": [
        "drone", "ड्रोन", "satellite", "precision farming",
        "latest", "nayi technology", "naya tarika", "2024", "2025",
        "app", "software", "artificial intelligence", "machine learning",
        "sensor", "iot", "smart farming", "aadhunik", "आधुनिक तकनीक"
    ],
    "disease": [
        "bimari", "बीमारी", "dhabbe", "धब्बे", "keede", "कीड़े",
        "pest", "fungus", "yellow", "peela", "पीला", "rot", "wilting"
    ],
    "weather": [
        "mausam", "मौसम", "barish", "बारिश", "temperature",
        "taapmaan", "तापमान", "forecast", "baarish"
    ],
    "mandi": [
        "bhav", "भाव", "price", "rate", "mandi", "मंडी",
        "market", "bechna", "बेचना"
    ],
    "schemes": [
        "yojana", "योजना", "scheme", "pm kisan", "subsidy",
        "sarkar", "सरकार", "loan", "registration", "apply"
    ]
}

SUPERVISOR_PROMPT = """You are a routing assistant. Reply with ONLY one word.

- disease  → crop disease, pest, yellowing, spots, insects
- weather  → rain, weather, temperature, irrigation timing  
- mandi    → price, rate, mandi, market, sell
- schemes  → government scheme, subsidy, loan, PM Kisan
- general  → everything else

Reply with ONLY one word."""

def supervisor_node(state: AgentState) -> AgentState:
    message_lower = state["message"].lower()

    # Check forced routing first — Python keyword matching
    # This is faster and more reliable than LLM for known keywords
    for tool, keywords in FORCED_ROUTING.items():
        for keyword in keywords:
            if keyword.lower() in message_lower:
                state["tool_to_use"] = tool
                return state

    # Fall back to LLM for everything else
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
    valid = {"disease", "weather", "mandi", "schemes", "general", "web_search"}
    if decision not in valid:
        decision = "general"

    state["tool_to_use"] = decision
    return state