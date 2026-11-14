import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any
import streamlit as st
from google import genai
from hdfs import InsecureClient

# Giữ nguyên import ML & RAG của bạn để dùng cho sau này
from src.core.ml_tools import ClassicalMLToolbox
from src.core.rag_engine import HybridRAGEngine

SYSTEM_INSTRUCTION = """Bạn là Reiner, một trợ lý AI doanh nghiệp thông minh, sắc sảo và chuyên nghiệp. 
Giải thích toán học dùng LaTeX, viết code chuẩn xác, ngắn gọn đi thẳng vào vấn đề."""

class EnterpriseAIAgent:
    def __init__(self):
        # Khởi tạo ML & RAG để dành sau này
        self.ml_toolbox = ClassicalMLToolbox()
        self.rag_engine = HybridRAGEngine()
        
        # Thiết lập kết nối Data Lake (HDFS)
        try:
            # Thay IP bằng địa chỉ Hadoop NameNode của bạn
            self.hdfs_client = InsecureClient('http://localhost:50070', user='hdfs')
            self.hdfs_log_path = '/user/hive/warehouse/datalake/reiner_logs/'
        except Exception as e:
            print(f"Lỗi khởi tạo HDFS: {e}")

    def log_to_datalake(self, session_id: str, username: str, role: str, content: str):
        """Đóng gói dữ liệu thành JSON và bắn lên thư mục Data Lake"""
        log_entry = {
            "session_id": session_id,
            "username": username,
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        # Đặt tên file log theo timestamp tới phần nghìn giây
        file_name = f"log_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
        
        try:
            full_path = os.path.join(self.hdfs_log_path, file_name)
            # Ghi file thẳng lên HDFS
            with self.hdfs_client.write(full_path, encoding='utf-8') as writer:
                json.dump(log_entry, writer)
        except Exception as e:
            # Try-except để bot vẫn chạy mượt mà ngay cả khi HDFS sập
            print(f"Chưa kết nối được HDFS (Log tạm bỏ qua): {e}")

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