import app.config  
# loads env vars and LangSmith setup first
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import chat

app = FastAPI(
    title="Kisaan AI",
    description="AI Farming Assistant for Rural India",
    version="1.0.0"
)

# This allows React frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Kisaan AI backend is running"}

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "kisaan-ai"}

app.include_router(chat.router, prefix="/api")
