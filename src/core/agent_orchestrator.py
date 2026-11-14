import os
import json
import io
from datetime import datetime
from typing import List, Dict, Any
import streamlit as st
from google import genai
from minio import Minio

SYSTEM_INSTRUCTION = """Bạn là Reiner, một trợ lý AI doanh nghiệp thông minh, sắc sảo và chuyên nghiệp. 
Giải thích toán học dùng LaTeX, viết code chuẩn xác, ngắn gọn đi thẳng vào vấn đề."""

class EnterpriseAIAgent:
    def __init__(self):
        # Thiết lập kết nối Data Lake (MinIO thay vì HDFS)
        try:
            # Lưu ý: "minio:9000" vì chúng ta chạy chung trong mạng Docker
            self.minio_client = Minio(
                "minio:9000",
                access_key="reineradmin",
                secret_key="reiner12345",
                secure=False
            )
            self.bucket_name = "reiner-logs"
            
            # Tự động tạo thư mục gốc (bucket) nếu chưa tồn tại
            if not self.minio_client.bucket_exists(self.bucket_name):
                self.minio_client.make_bucket(self.bucket_name)
                print(f"Đã tạo thùng chứa Data Lake: {self.bucket_name}")
                
        except Exception as e:
            print(f"Lỗi khởi tạo MinIO: {e}")

    def log_to_datalake(self, session_id: str, username: str, role: str, content: str):
        """Đóng gói dữ liệu thành JSON và bắn thẳng lên MinIO"""
        log_entry = {
            "session_id": session_id,
            "username": username,
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        file_name = f"chat_logs/log_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
        
        try:
            # Chuyển đổi dict thành luồng byte để MinIO lưu trữ
            json_bytes = json.dumps(log_entry, ensure_ascii=False).encode('utf-8')
            json_stream = io.BytesIO(json_bytes)
            
            # Ghi file thẳng lên Data Lake
            self.minio_client.put_object(
                bucket_name=self.bucket_name,
                object_name=file_name,
                data=json_stream,
                length=len(json_bytes),
                content_type="application/json"
            )
        except Exception as e:
            print(f"Chưa kết nối được MinIO (Log tạm bỏ qua): {e}")

    def chat_stream(
        self,
        user_message: str,
        history: List[Dict[str, Any]],
        session_id: str,
        username: str
    ) -> Dict[str, Any]:
        
        # 1. Ghi log lời nhắn của người dùng xuống Data Lake
        self.log_to_datalake(session_id, username, "user", user_message)

        try:
            # Lấy API Key an toàn
            api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
            client = genai.Client(api_key=api_key)

            # Đọc lại lịch sử 
            context_str = ""
            for msg in history[-10:]:
                role_name = username if msg.get("role") == "user" else "Reiner"
                context_str += f"{role_name}: {msg.get('content', '')}\n"
            
            final_prompt = f"{context_str}\n{username}: {user_message}"

            # Gọi Gemini API thuần túy
            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=final_prompt,
                config={"system_instruction": SYSTEM_INSTRUCTION}
            )

            # 2. Ghi log phản hồi của AI xuống Data Lake
            self.log_to_datalake(session_id, username, "model", response.text)

            return {"reply": response.text}

        except Exception as e:
            error_msg = f"*(Lỗi kết nối AI: {str(e)})*"
            self.log_to_datalake(session_id, username, "error", error_msg)
            return {"reply": error_msg}