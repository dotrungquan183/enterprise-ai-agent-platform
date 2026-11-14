from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from src.core.agent_orchestrator import EnterpriseAIAgent

app = FastAPI(title="Enterprise Hybrid Chat AI Backend")
agent = EnterpriseAIAgent()

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []
    provider: Optional[str] = "auto"
    api_key: Optional[str] = ""

@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    return agent.chat(req.message, req.history, req.provider, req.api_key)
