# web_search.py
# Uses Tavily to search the web in real time
# Called when farmer asks something our other tools don't cover
# Example: new government schemes, rare diseases, current news

from app.agent.state import AgentState
from app.config import TAVILY_API_KEY
from tavily import TavilyClient

client = TavilyClient(api_key=TAVILY_API_KEY)

def web_search_tool(state: AgentState) -> AgentState:
    query = state["message"]
    
    try:
        # Search with focus on Indian farming context
        result = client.search(
            query=f"Indian farmer {query}",
            search_depth="basic",
            max_results=3,
            include_answer=True
        )
        
        # Tavily returns a direct answer + source results
        answer = result.get("answer", "")
        sources = result.get("results", [])
        
        # Build result text
        if answer:
            content = f"Web search answer: {answer}\n\n"
        else:
            content = ""
            
        # Add top 2 source snippets
        for source in sources[:2]:
            snippet = source.get("content", "")[:300]
            content += f"Source: {snippet}\n\n"
            
        state["tool_result"] = content if content else "No relevant information found online."
        
    except Exception as e:
        state["tool_result"] = "Web search unavailable right now. Please try again."
    
    return state