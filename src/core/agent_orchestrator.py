import os
import json
import requests
from datetime import datetime
from typing import List, Dict, Any

class EnterpriseAIAgent:
    def __init__(self):
        self.http_session = requests.Session()
        
        # Đọc trực tiếp từ biến môi trường .env (hoặc Streamlit Secrets)
        self.tunnel_url = os.getenv(
            "LOCAL_TUNNEL_URL", 
            "https://wise-sorry-estimated-pollution.trycloudflare.com/generate"
        )

        self.supabase_url = os.getenv("SUPABASE_URL", "https://pehksvqnwpemeifpjnnx.supabase.co/rest/v1/chat_logs")
        self.supabase_key = os.getenv("SUPABASE_KEY", "").strip()
        self.supabase_headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }

    def log_to_datalake(self, session_id: str, username: str, role: str, content: str):
        log_entry = {
            "session_id": str(session_id),
            "username": str(username),
            "role": str(role),
            "content": str(content),
            "timestamp": datetime.now().isoformat(),
            "is_synced": False
        }
        try:
            res = self.http_session.post(self.supabase_url, headers=self.supabase_headers, json=log_entry, timeout=5)
            if res.status_code < 400:
                try:
                    from src.core.minio_sync import sync_supabase_to_minio
                    sync_supabase_to_minio()
                except Exception:
                    pass
                return
        except Exception:
            pass

    def chat_stream(
        self,
        user_message: str,
        history: List[Dict[str, Any]],
        session_id: str,
        username: str,
        api_key_override: str = None
    ) -> Dict[str, Any]:
        self.log_to_datalake(session_id, username, "user", user_message)

        try:
            context_str = ""
            for msg in history[-6:]:
                r_type = msg.get("role", "user")
                c_text = msg.get("content", "")
                role_name = username if r_type == "user" else "Reiner"
                context_str += f"{role_name}: {c_text}\n"

            final_prompt = f"{context_str}\n{username}: {user_message}".strip()
            system_instruction = "Bạn là Reiner, trợ lý AI doanh nghiệp thông minh, sắc sảo. Giải thích toán học dùng LaTeX."

            payload = {
                "prompt": final_prompt,
                "system_instruction": system_instruction
            }

            # Gửi yêu cầu qua Cloudflare Tunnel về máy cá nhân
            response = self.http_session.post(self.tunnel_url, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                reply_text = data.get("reply", "Không nhận được phản hồi từ Local AI.")
            else:
                reply_text = f"*(Lỗi Tunnel HTTP {response.status_code})*"

            self.log_to_datalake(session_id, username, "model", reply_text)
            return {"reply": reply_text}

        except Exception as e:
            error_msg = f"*(Lỗi kết nối Local AI: {str(e)})*"
            self.log_to_datalake(session_id, username, "error", error_msg)
            return {"reply": error_msg}

_GLOBAL_AGENT_INSTANCE = None
def get_global_agent() -> EnterpriseAIAgent:
    global _GLOBAL_AGENT_INSTANCE
    if _GLOBAL_AGENT_INSTANCE is None:
        _GLOBAL_AGENT_INSTANCE = EnterpriseAIAgent()
    return _GLOBAL_AGENT_INSTANCE