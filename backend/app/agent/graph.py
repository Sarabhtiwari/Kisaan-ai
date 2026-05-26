from langgraph.graph import StateGraph, END
from langgraph.types import Send
from app.agent.state import AgentState
from app.agent.supervisor import supervisor_node
from app.tools.disease_detection import disease_node
from app.tools.web_search import web_search_tool
from app.tools.schemes_rag import schemes_rag_tool
import httpx

# --- Tool node functions ---

def weather_node(state: AgentState) -> AgentState:
    location = state.get("location") or {}
    city = location.get("city", "Lucknow")
    try:
        response = httpx.get(f"https://wttr.in/{city}?format=j1", timeout=5)
        data = response.json()
        current = data["current_condition"][0]
        temp = current["temp_C"]
        desc = current["weatherDesc"][0]["value"]
        humidity = current["humidity"]
        result = f"Temperature: {temp}°C, Weather: {desc}, Humidity: {humidity}%"
    except:
        result = "Weather data unavailable right now."
    state["tool_result"] = result
    state["tool_results"] = [result]
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
            "rising": "badh raha hai ↑",
            "falling": "gir raha hai ↓",
            "stable": "sthir hai →"
        }.get(data["trend"], "")
        result = (
            f"{crop_name.capitalize()} ka bhav aaj Lucknow mandi mein: "
            f"Rs {data['price']} per {data['unit']}. "
            f"Bhav {trend_text}."
        )
    else:
        result = "Is fasal ka bhav available nahi hai. gehu, chawal, sarso, aloo mein se koi naam likhein."
    state["tool_result"] = result
    state["tool_results"] = [result]
    return state

def schemes_node(state: AgentState) -> AgentState:
    result = schemes_rag_tool(state)
    result["tool_results"] = [result["tool_result"]]
    return result

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
        SystemMessage(content="You are an expert farming assistant for Indian farmers."),
        HumanMessage(content=state["message"])
    ])
    result = response.content
    state["tool_result"] = result
    state["tool_results"] = [result]
    return state

def disease_tool_node(state: AgentState) -> AgentState:
    result = disease_node(state)
    result["tool_results"] = [result["tool_result"]]
    return result

def web_search_node(state: AgentState) -> AgentState:
    result = web_search_tool(state)
    result["tool_results"] = [result["tool_result"]]
    return result

# --- Parallel routing function ---
# This is the key function for parallelization
# Instead of returning one node name, it returns
# multiple Send objects — one per tool
# LangGraph runs all of them simultaneously

def route_to_tools(state: AgentState):
    tools_to_use = state.get("tools_to_use", [])

    # Map tool name to node name
    tool_map = {
        "weather":    "weather",
        "mandi":      "mandi",
        "disease":    "disease",
        "schemes":    "schemes",
        "general":    "general",
        "web_search": "web_search",
    }

    if not tools_to_use:
        return [Send("general", state)]

    # Send to all matched tools simultaneously
    return [
        Send(tool_map.get(tool, "general"), state)
        for tool in tools_to_use
        if tool in tool_map
    ]

# --- Build the graph ---

def build_graph():
    graph = StateGraph(AgentState)

    # Add all nodes
    graph.add_node("supervisor",  supervisor_node)
    graph.add_node("weather",     weather_node)
    graph.add_node("mandi",       mandi_node)
    graph.add_node("disease",     disease_tool_node)
    graph.add_node("schemes",     schemes_node)
    graph.add_node("general",     general_node)
    graph.add_node("web_search",  web_search_node)

    # Entry point
    graph.set_entry_point("supervisor")

    # Supervisor uses Send API to route to one or more tools
    graph.add_conditional_edges(
        "supervisor",
        route_to_tools,   # returns list of Send objects
        [                 # all possible destination nodes
            "weather",
            "mandi",
            "disease",
            "schemes",
            "general",
            "web_search"
        ]
    )

    # All tools go to END
    # Synthesizer is handled in chat.py for streaming
    for tool in ["weather", "mandi", "disease", "schemes", "general", "web_search"]:
        graph.add_edge(tool, END)

    return graph.compile()

agent = build_graph()