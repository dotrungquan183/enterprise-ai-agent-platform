from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from src.core.agent_orchestrator import EnterpriseAIAgent

app = FastAPI(title="Enterprise Hybrid Chat AI Backend")
agent = EnterpriseAIAgent()

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []
    session_id: Optional[str] = "default_session" # Bổ sung session_id
    username: Optional[str] = "quan"             # Bổ sung username mặc định

@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    # Gọi đúng hàm chat_stream đã được tích hợp MinIO Data Lake
    return agent.chat_stream(
        user_message=req.message,
        history=req.history,
        session_id=req.session_id,
        username=req.username
    )