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
    mandi_data = {
        "gehu": {"price": "2150-2200", "unit": "quintal", "trend": "stable"},
        "wheat": {"price": "2150-2200", "unit": "quintal", "trend": "stable"},
        "chawal": {"price": "3200-3500", "unit": "quintal", "trend": "rising"},
        "rice": {"price": "3200-3500", "unit": "quintal", "trend": "rising"},
        "dhan": {"price": "2800-3000", "unit": "quintal", "trend": "stable"},
        "makka": {"price": "1800-1950", "unit": "quintal", "trend": "falling"},
        "maize": {"price": "1800-1950", "unit": "quintal", "trend": "falling"},
        "sarso": {"price": "5200-5400", "unit": "quintal", "trend": "rising"},
        "mustard": {"price": "5200-5400", "unit": "quintal", "trend": "rising"},
        "aloo": {"price": "800-1200", "unit": "quintal", "trend": "falling"},
        "potato": {"price": "800-1200", "unit": "quintal", "trend": "falling"},
        "pyaz": {"price": "1500-2000", "unit": "quintal", "trend": "stable"},
        "onion": {"price": "1500-2000", "unit": "quintal", "trend": "stable"},
        "tamatar": {"price": "600-1000", "unit": "quintal", "trend": "falling"},
        "tomato": {"price": "600-1000", "unit": "quintal", "trend": "falling"},
        "chana": {"price": "4800-5100", "unit": "quintal", "trend": "stable"},
        "soybean": {"price": "3800-4000", "unit": "quintal", "trend": "rising"},
    }

    message = state["message"].lower()
    found = None

    for crop, data in mandi_data.items():
        if crop in message:
            found = (crop, data)
            break

    if found:
        crop_name, data = found
        trend_text = {
            "rising": "बढ़ रहा है ↑",
            "falling": "गिर रहा है ↓",
            "stable": "स्थिर है →"
        }.get(data["trend"], "")

        state["tool_result"] = (
            f"{crop_name.capitalize()} ka bhav aaj Lucknow mandi mein: "
            f"Rs {data['price']} per {data['unit']}. "
            f"Bhav {trend_text}. "
            f"Sahi samay par bechne ke liye apne nazdiki mandi agent se sampark karein."
        )
    else:
        state["tool_result"] = (
            "Is fasal ka bhav abhi available nahi hai. "
            "Kripaya gehu, chawal, makka, sarso, aloo, pyaz, tamatar, chana "
            "mein se kisi ka naam likhein. "
            "Ya agmarknet.nic.in par check karein."
        )

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