import os
import json
import io
import socket
import requests
import urllib3
from datetime import datetime
from typing import List, Dict, Any
from minio import Minio

# --- ÉP PYTHON DÙNG IPV4 ĐỂ TRÁNH LỖI READ TIMED OUT TRÊN WINDOWS ---
urllib3.util.connection.allowed_gai_family = lambda: socket.AF_INET

SYSTEM_INSTRUCTION = """Bạn là Reiner, một trợ lý AI doanh nghiệp thông minh, sắc sảo và chuyên nghiệp. 
Giải thích toán học dùng LaTeX, viết code chuẩn xác, ngắn gọn đi thẳng vào vấn đề."""


class EnterpriseAIAgent:
    def __init__(self):
        self.bucket_name = "reiner-logs"
        self.minio_client = None
        self.http_session = requests.Session()

        minio_endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        access_key = os.getenv("MINIO_ACCESS_KEY", "reineradmin")
        secret_key = os.getenv("MINIO_SECRET_KEY", "reiner12345")

        try:
            http_client = urllib3.PoolManager(timeout=urllib3.Timeout(connect=1.0, read=1.0))
            client = Minio(
                minio_endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=False,
                http_client=http_client
            )
            if not client.bucket_exists(self.bucket_name):
                client.make_bucket(self.bucket_name)
            self.minio_client = client
        except Exception:
            self.minio_client = None

    def log_to_datalake(self, session_id: str, username: str, role: str, content: str):
        if self.minio_client is None:
            return

        log_entry = {
            "session_id": str(session_id),
            "username": str(username),
            "role": str(role),
            "content": str(content),
            "timestamp": datetime.now().isoformat()
        }

        file_name = f"chat_logs/log_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"

        try:
            json_bytes = json.dumps(log_entry, ensure_ascii=False).encode("utf-8")
            json_stream = io.BytesIO(json_bytes)

            self.minio_client.put_object(
                bucket_name=self.bucket_name,
                object_name=file_name,
                data=json_stream,
                length=len(json_bytes),
                content_type="application/json"
            )
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
            # Chỉ lấy key từ ô nhập trên giao diện hoặc biến môi trường (KHÔNG gán cứng key trong code)
            active_key = (
                api_key_override.strip()
                if (api_key_override and api_key_override.strip())
                else os.getenv("GEMINI_API_KEY", "").strip()
            )

            if not active_key:
                return {
                    "reply": "⚠️ **Chưa có API Key!** Vui lòng dán Gemini API Key của bạn vào ô **🔑 Gemini API Key** ở thanh công cụ bên trái rồi nhấn Enter."
                }

            context_str = ""
            for msg in history[-10:]:
                r_type = msg.get("role", "user")
                c_text = msg.get("content", "")
                role_name = username if r_type == "user" else "Reiner"
                context_str += f"{role_name}: {c_text}\n"

            final_prompt = f"{context_str}\n{username}: {user_message}".strip()

            headers = {
                "Content-Type": "application/json",
                "X-goog-api-key": active_key
            }
            payload = {
                "system_instruction": {
                    "parts": [{"text": SYSTEM_INSTRUCTION}]
                },
                "contents": [
                    {
                        "parts": [{"text": final_prompt}]
                    }
                ]
            }

            models_to_try = [
                "gemini-3.5-flash",
                "gemini-3.5-pro",
                "gemini-flash-latest",
                "gemini-2.5-flash"
            ]
            last_error = None

            for model_name in models_to_try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
                try:
                    res = self.http_session.post(url, headers=headers, json=payload, timeout=(10, 60))
                    
                    if res.status_code == 200:
                        data = res.json()
                        candidates = data.get("candidates", [])
                        if candidates and "content" in candidates[0]:
                            parts = candidates[0]["content"].get("parts", [])
                            reply_text = "".join(p.get("text", "") for p in parts)
                        else:
                            reply_text = "Không có phản hồi từ mô hình."

                        self.log_to_datalake(session_id, username, "model", reply_text)
                        return {"reply": reply_text}
                    elif res.status_code == 404:
                        continue
                    else:
                        raise RuntimeError(f"HTTP {res.status_code} ({model_name}) - {res.text}")
                except Exception as req_err:
                    last_error = f"{model_name}: {str(req_err)}"
                    continue

            raise RuntimeError(last_error or "Không thể kết nối tới máy chủ Gemini.")

        except Exception as e:
            error_msg = f"*(Lỗi kết nối AI: {str(e)})*"
            self.log_to_datalake(session_id, username, "error", error_msg)
            return {"reply": error_msg}


_GLOBAL_AGENT_INSTANCE = None

def get_global_agent() -> EnterpriseAIAgent:
    global _GLOBAL_AGENT_INSTANCE
    if _GLOBAL_AGENT_INSTANCE is None:
        _GLOBAL_AGENT_INSTANCE = EnterpriseAIAgent()
    return _GLOBAL_AGENT_INSTANCE