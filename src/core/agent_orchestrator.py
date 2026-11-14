import os
import json
from typing import List, Dict, Any
import streamlit as st
from google import genai
from src.core.ml_tools import ClassicalMLToolbox
from src.core.rag_engine import HybridRAGEngine

SYSTEM_INSTRUCTION = """Bạn là một Trợ lý AI Doanh nghiệp (Enterprise AI Collaborator) cực kỳ thông minh, sắc sảo và chuyên nghiệp. 
Bạn có phong cách trò chuyện tự nhiên, biết giải thích toán học (dùng LaTeX), viết code và phân tích dữ liệu.

Hệ thống của bạn có tích hợp các cơ sở dữ liệu và mô hình Machine Learning sau:
- Khách hàng mẫu: CUST_001 (nguy cơ rời bỏ cao), CUST_002 (VIP Kim Cương), CUST_003 (Vàng ổn định).
- Bạn hãy trả lời câu hỏi của người dùng một cách thuyết phục nhất. Nếu người dùng hỏi về dữ liệu khách hàng cụ thể hoặc gợi ý mua kèm, hãy chủ động phân tích các chiều số liệu (PCA, K-Means, CLV, Churn, FP-Growth).
"""

class EnterpriseAIAgent:
    def __init__(self):
        self.ml_toolbox = ClassicalMLToolbox()
        self.rag_engine = HybridRAGEngine()

    def chat_stream(
        self,
        user_message: str,
        history: List[Dict[str, Any]],
        provider: str = "gemini",
        api_key: str = "",
        model_name: str = "gemini-3.5-flash"  # Sử dụng đúng phiên bản 3.5-flash chuẩn xác
    ) -> Dict[str, Any]:
        
        msg_lower = user_message.lower()
        
        # 1. Phát hiện ý định gọi ML Tools
        tools_called = []
        ml_context_data = []

        if any(k in msg_lower for k in ["cust_", "khách hàng", "churn", "rời bỏ", "clv", "phân khúc"]):
            cid = "CUST_001"
            if "cust_002" in msg_lower: cid = "CUST_002"
            elif "cust_003" in msg_lower: cid = "CUST_003"
            
            res = self.ml_toolbox.analyze_customer_tool(cid)
            tools_called.append({"tool_name": "analyze_customer_360", "arguments": {"customer_id": cid}})
            ml_context_data.append(res)

        if any(k in msg_lower for k in ["mua kèm", "gợi ý", "laptop", "smartphone", "fp-growth"]):
            item = "Laptop" if "laptop" in msg_lower else "Smartphone"
            res = self.ml_toolbox.recommend_cross_sell_tool(item)
            tools_called.append({"tool_name": "recommend_cross_sell_fpgrowth", "arguments": {"item_name": item}})
            ml_context_data.append(res)

        # 2. Truy xuất RAG
        rag_docs = self.rag_engine.retrieve(user_message, top_k=1)

        # 3. Lấy API key an toàn từ st.secrets hoặc os.getenv
        try:
            resolved_key = api_key.strip() if api_key else ""
            if not resolved_key:
                try:
                    resolved_key = st.secrets.get("GEMINI_API_KEY", "")
                except Exception:
                    pass
            if not resolved_key:
                resolved_key = os.getenv("GEMINI_API_KEY", "")

            if not resolved_key:
                return self._fallback_response(user_message, ml_context_data, rag_docs)

            # Khởi tạo client chuẩn của thư viện google-genai
            client = genai.Client(api_key=resolved_key)
            target_model = model_name if model_name else "gemini-3.5-flash"

            # Xây dựng lịch sử chat theo định dạng của SDK mới
            chat_history = []
            for msg in history[-6:]:
                role = "user" if msg["role"] == "user" else "model"
                chat_history.append({"role": role, "parts": [msg["content"]]})

            # Ghép thêm ngữ cảnh ML/RAG vào tin nhắn nếu có
            final_prompt = user_message
            if ml_context_data or rag_docs:
                context_str = "[Dữ liệu Hệ thống]\n"
                if ml_context_data:
                    context_str += f"ML Data: {json.dumps(ml_context_data, ensure_ascii=False)}\n"
                if rag_docs:
                    context_str += f"RAG Doc: {rag_docs[0]['chunk_content']}\n"
                final_prompt = f"{context_str}\nCâu hỏi người dùng: {user_message}"

            # Gọi API qua client.chats
            chat = client.chats.create(model=target_model, history=chat_history)
            response = chat.send_message(final_prompt)

            return {
                "reply": response.text,
                "engine_used": f"Google Gemini ({target_model}) + ML Tools + RAG",
                "tools_called": tools_called,
            }

        except Exception as e:
            fallback = self._fallback_response(user_message, ml_context_data, rag_docs)
            fallback["reply"] = f"⚠️ *(Lỗi gọi Gemini API: {str(e)})*\n\n" + fallback["reply"]
            return fallback

    def _fallback_response(self, user_message, ml_context_data, rag_docs) -> Dict[str, Any]:
        reply_lines = ["### 🤖 Phản hồi từ Hệ thống Hybrid AI (Offline Mode)\n"]
        if ml_context_data:
            reply_lines.append(f"**Kết quả phân tích từ Mô hình Machine Learning:**\n```json\n{json.dumps(ml_context_data, ensure_ascii=False, indent=2)}\n```")
        if rag_docs:
            reply_lines.append(f"**Tài liệu RAG liên quan:**\n> {rag_docs[0]['chunk_content']}")
        return {
            "reply": "\n".join(reply_lines),
            "engine_used": "Hybrid Rule-based Fallback",
            "tools_called": []
        }