import os
import json
import socket
import requests
import urllib3
from datetime import datetime
from typing import List, Dict, Any

# Ép buộc Python dùng IPv4 cho các kết nối mạng ổn định trên Windows
urllib3.util.connection.allowed_gai_family = lambda: socket.AF_INET

SYSTEM_INSTRUCTION = """Bạn là Reiner, một trợ lý AI doanh nghiệp thông minh, sắc sảo và chuyên nghiệp. 
Giải thích toán học dùng LaTeX, viết code chuẩn xác, ngắn gọn đi thẳng vào vấn đề."""


class EnterpriseAIAgent:
    def __init__(self):
        self.http_session = requests.Session()

        # Cấu hình Supabase REST API với Project ID chuẩn xác
        self.supabase_url = "https://pehksvqnwpemeifpjnnx.supabase.co/rest/v1/chat_logs"
        self.supabase_key = "sb_secret_vYEq1KruST1kdmqk4z1Rog_K205n-Or"
        self.supabase_headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }

    def log_to_datalake(self, session_id: str, username: str, role: str, content: str):
        """Hàm ghi log trực tiếp lên Supabase"""
        log_entry = {
            "session_id": str(session_id),
            "username": str(username),
            "role": str(role),
            "content": str(content),
            "timestamp": datetime.now().isoformat(),
            "is_synced": False
        }

        try:
            res = self.http_session.post(
                self.supabase_url, 
                headers=self.supabase_headers, 
                json=log_entry, 
                timeout=5
            )
            if res.status_code < 400:
                print("✅ [Supabase] Đã ghi log thành công lên mây!")
            else:
                print(f"⚠️ [Supabase] Lỗi HTTP {res.status_code}: {res.text}")
        except Exception as e:
            print(f"⚠️ [Supabase] Lỗi kết nối: {e}")

        # Fallback lưu dự phòng local nếu mất mạng đột xuất
        try:
            backup_file = "local_chat_backup.json"
            existing_data = []
            if os.path.exists(backup_file):
                with open(backup_file, "r", encoding="utf-8") as f:
                    try:
                        existing_data = json.load(f)
                    except:
                        existing_data = []
            existing_data.append(log_entry)
            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
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
            active_key = (
                api_key_override.strip()
                if (api_key_override and api_key_override.strip())
                else os.getenv("GEMINI_API_KEY", "").strip()
            )

            if not active_key:
                return {
                    "reply": "⚠️ **Chưa có API Key!** Vui lòng dán Gemini API Key vào ô **🔑 Gemini API Key** ở thanh công cụ bên trái rồi nhấn Enter."
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

            # Ưu tiên quét model 3.5 trước
            models_to_try = [
                "gemini-3.5-flash",
                "gemini-3.5-pro",
                "gemini-1.5-flash",
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
                    elif res.status_code in [404, 429]:
                        continue
                    else:
                        raise RuntimeError(f"HTTP {res.status_code} ({model_name}) - {res.text}")
                except Exception as req_err:
                    last_error = f"{model_name}: {str(req_err)}"
                    continue

            raise RuntimeError(last_error or "Không thể kết nối tới máy chủ Gemini hoặc đã cạn hạn mức quota toàn bộ model.")

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