from langgraph.graph import StateGraph, END
from app.agent.state import AgentState
from app.agent.supervisor import supervisor_node
from app.agent.synthesizer import synthesizer_node
from app.tools.disease_detection import disease_node
# --- Tool nodes (simple for now, we upgrade these one by one) ---

def weather_node(state: AgentState) -> AgentState:
    import httpx
    location = state.get("location") or {}
    city = location.get("city", "Lucknow")
    
    try:
        response = httpx.get(f"https://wttr.in/{city}?format=j1", timeout=5)
        data = response.json()
        current = data["current_condition"][0]
        temp = current["temp_C"]
        desc = current["weatherDesc"][0]["value"]
        humidity = current["humidity"]
        state["tool_result"] = f"Temperature: {temp}°C, Weather: {desc}, Humidity: {humidity}%"
    except:
        state["tool_result"] = "Weather data unavailable right now."
    
    return state

def mandi_node(state: AgentState) -> AgentState:
    state["tool_result"] = "Mandi price tool coming soon. Check your local mandi or agmarknet.nic.in for today's prices."
    return state

def schemes_node(state: AgentState) -> AgentState:
    state["tool_result"] = "Government schemes tool coming soon. Key schemes: PM Kisan (6000/year), Fasal Bima Yojana (crop insurance), KCC (Kisan Credit Card)."
    return state

def general_node(state: AgentState) -> AgentState:
    from app.config import GROQ_API_KEY
    from langchain_groq import ChatGroq
    from langchain_core.messages import HumanMessage, SystemMessage
    
    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model="llama-3.3-70b-versatile",
        temperature=0.4
    )
    
    response = llm.invoke([
        SystemMessage(content="You are an expert farming assistant for Indian farmers. Answer practically and simply."),
        HumanMessage(content=state["message"])
    ])
    
    state["tool_result"] = response.content
    return state

# --- Build the graph ---

def build_graph():
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("supervisor",  supervisor_node)
    graph.add_node("disease",     disease_node)
    graph.add_node("weather",     weather_node)
    graph.add_node("mandi",       mandi_node)
    graph.add_node("schemes",     schemes_node)
    graph.add_node("general",     general_node)
    graph.add_node("synthesizer", synthesizer_node)

    # Entry point
    graph.set_entry_point("supervisor")

    # Supervisor routes to correct tool
    graph.add_conditional_edges(
        "supervisor",
        lambda state: state["tool_to_use"],
        {
            "disease":  "disease",
            "weather":  "weather",
            "mandi":    "mandi",
            "schemes":  "schemes",
            "general":  "general",
        }
    )

    # Every tool goes to synthesizer after
    for tool in ["disease", "weather", "mandi", "schemes", "general"]:
        graph.add_edge(tool, "synthesizer")

    # Synthesizer is the last step
    graph.add_edge("synthesizer", END)

    return graph.compile()

# Compile once when server starts
agent = build_graph()