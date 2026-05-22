from app.agent.state import AgentState
from app.config import GEMINI_API_KEY
from google import genai
from google.genai import types
import base64

# New google.genai client style
client = genai.Client(api_key=GEMINI_API_KEY)

DISEASE_PROMPT = """You are an expert agricultural scientist specializing in crop diseases.

Analyze this crop image carefully. Even if the image is slightly blurry or unclear, 
do your best to identify what you can see and give helpful advice.

Provide:
1. What disease or pest problem you can see (or likely see)
2. How severe it looks
3. Possible cause
4. Treatment steps in simple language

Always try to give some useful answer even from an unclear image.
Never refuse to answer just because image is slightly blurry.
If you truly cannot see anything plant-related at all, then only ask for another photo."""

def disease_node(state: AgentState) -> AgentState:
    image_base64 = state.get("image_base64")

    if not image_base64:
        state["tool_result"] = "No image received. Please send a photo of your crop for disease analysis."
        return state

    try:
        image_data = base64.b64decode(image_base64)

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[
                DISEASE_PROMPT,
                types.Part.from_bytes(
                    data=image_data,
                    mime_type="image/jpeg"
                )
            ]
        )

        state["tool_result"] = response.text

    except Exception as e:
        state["tool_result"] = "Could not analyze image. Please try again with a clearer photo."

    return state