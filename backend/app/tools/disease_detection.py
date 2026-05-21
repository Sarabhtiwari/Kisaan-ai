from app.agent.state import AgentState
from app.config import GEMINI_API_KEY
import google.generativeai as genai
import base64

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

DISEASE_PROMPT = """You are an expert agricultural scientist specializing in crop diseases.

Analyze this crop image carefully and provide:
1. What disease or pest problem you can see
2. How severe it is (mild/moderate/severe)
3. What caused it
4. Treatment steps in simple language

If the image is not a crop or plant, say "Please send a clear photo of your crop."
Be specific and practical. A farmer will read this."""

def disease_node(state: AgentState) -> AgentState:
    image_base64 = state.get("image_base64")
    
    # If no image sent, give general advice
    if not image_base64:
        state["tool_result"] = "No image received. Please send a photo of your crop for disease analysis."
        return state
    
    try:
        # Decode the base64 image
        image_data = base64.b64decode(image_base64)
        
        # Send image to Gemini
        response = model.generate_content([
            DISEASE_PROMPT,
            {
                "mime_type": "image/jpeg",
                "data": image_data
            }
        ])
        
        state["tool_result"] = response.text
        
    except Exception as e:
        state["tool_result"] = f"Could not analyze image. Please try again with a clearer photo."
    
    return state