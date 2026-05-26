from app.agent.state import AgentState
from app.config import GROQ_API_KEY
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.3-70b-versatile",
    temperature=0
)

# Keywords that force specific tools
FORCED_ROUTING = {
    "web_search": [
        "drone", "ड्रोन", "satellite", "precision farming",
        "latest", "nayi technology", "naya tarika", "2024", "2025",
        "app", "software", "sensor", "iot", "smart farming", "aadhunik"
    ],
    "disease": [
        "bimari", "बीमारी", "dhabbe", "धब्बे", "keede", "कीड़े",
        "pest", "fungus", "peela", "पीला", "rot", "spots"
    ],
    "weather": [
        "mausam", "मौसम", "barish", "बारिश", "temperature",
        "taapmaan", "तापमान", "forecast", "baarish", "garmi", "sardi"
    ],
    "mandi": [
        "bhav", "भाव", "price", "rate", "mandi", "मंडी",
        "market", "bechna", "बेचना", "bikri"
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

    # Detect ALL matching tools from keywords
    matched_tools = []
    for tool, keywords in FORCED_ROUTING.items():
        for keyword in keywords:
            if keyword.lower() in message_lower:
                if tool not in matched_tools:
                    matched_tools.append(tool)
                break

    # If multiple tools detected — parallel execution
    if len(matched_tools) > 1:
        state["tools_to_use"] = matched_tools
        state["tool_to_use"] = matched_tools[0]  # fallback
        state["tool_results"] = []
        return state

    # If one tool detected from keywords
    if len(matched_tools) == 1:
        state["tools_to_use"] = matched_tools
        state["tool_to_use"] = matched_tools[0]
        state["tool_results"] = []
        return state

    # No keyword match — use LLM
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

    state["tools_to_use"] = [decision]
    state["tool_to_use"] = decision
    state["tool_results"] = []
    return state