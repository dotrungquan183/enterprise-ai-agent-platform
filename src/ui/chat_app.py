import sys
import os

# --- FIX LỖI ĐƯỜNG DẪN IMPORT (No module named 'src') ---
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

import streamlit as st
import uuid
import json
from datetime import datetime
from minio import Minio
from dotenv import load_dotenv
from src.core.agent_orchestrator import get_global_agent

load_dotenv()

# --- CẤU HÌNH MINIO CLIENT ---
endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
access_key = os.getenv("MINIO_ACCESS_KEY", "reineradmin")
secret_key = os.getenv("MINIO_SECRET_KEY", "reiner12345")
bucket_name = os.getenv("MINIO_BUCKET_NAME", "reiner-logs")

# Làm sạch endpoint (bỏ tiền tố http/https nếu có)
if endpoint.startswith("https://"):
    endpoint = endpoint.replace("https://", "")
elif endpoint.startswith("http://"):
    endpoint = endpoint.replace("http://", "")

is_local = "localhost" in endpoint or "127.0.0.1" in endpoint
secure_flag = not is_local

@st.cache_resource
def get_minio_client():
    return Minio(
        endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure_flag
    )

# --- CÁC HÀM TRUY VẤN LỊCH SỬ TỪ MINIO LOCAL ---
def fetch_all_sessions():
    """Liệt kê danh sách các session_id duy nhất từ MinIO"""
    try:
        client = get_minio_client()
        if not client.bucket_exists(bucket_name):
            return []
        
        objects = client.list_objects(bucket_name, prefix="chat_logs/", recursive=True)
        sessions = set()
        for obj in objects:
            file_basename = os.path.basename(obj.object_name)
            if file_basename.startswith("auto_pull_"):
                # Tách lấy phần UUID session giữa 'auto_pull_' và mốc thời gian _2026...
                parts = file_basename.replace("auto_pull_", "").split("_202")
                if len(parts) > 0:
                    sessions.add(parts[0])
        return sorted(list(sessions), reverse=True)
    except Exception as e:
        return []

def load_messages_by_session(target_session_id):
    """Tải toàn bộ tin nhắn của một session cụ thể từ các file JSON trên MinIO"""
    try:
        client = get_minio_client()
        objects = client.list_objects(bucket_name, prefix="chat_logs/", recursive=True)
        session_logs = []
        
        count_files = 0
        for obj in objects:
            if target_session_id in obj.object_name:
                count_files += 1
                response = client.get_object(bucket_name, obj.object_name)
                try:
                    raw_data = response.read().decode('utf-8')
                    data = json.loads(raw_data)
                    
                    if isinstance(data, list):
                        session_logs.extend(data)
                    elif isinstance(data, dict):
                        session_logs.append(data)
                finally:
                    response.close()
        
        # IN THÔNG BÁO RA MÀN HÌNH ĐỂ CHECK TRỰC QUAN
        st.info(f"🔍 Đã quét thấy {count_files} file khớp với session. Tổng số log thô gom được: {len(session_logs)}")
                
        formatted_messages = []
        for msg in session_logs:
            role = msg.get("role", "user")
            if role == "model":
                role = "assistant"
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            
            if content:
                formatted_messages.append({
                    "role": role, 
                    "content": content,
                    "timestamp": timestamp
                })
                
        st.info(f"✨ Số tin nhắn sau khi format để vẽ lên UI: {len(formatted_messages)}")
        return sorted(formatted_messages, key=lambda x: x.get("timestamp", ""))
    except Exception as e:
        st.error(f"Lỗi code: {e}")
        return []
    
# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Reiner AI", page_icon="✨", layout="wide")
st.markdown("""
    <style>
        .block-container { padding-top: 2rem; padding-bottom: 0rem; }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 1. MÔ PHỎNG DATABASE USER ---
USERS_DB = {
    "quan": {"name": "Đỗ Trung Quân", "password": "123", "role": "admin"},
    "guest": {"name": "Khách mời", "password": "abc", "role": "user"}
}

# --- 2. HỆ THỐNG ĐĂNG NHẬP & PHÂN QUYỀN ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h2 style='text-align: center; margin-top: 50px;'>Đăng nhập Hệ thống AI</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Tài khoản (thử 'quan' hoặc 'guest')")
            password = st.text_input("Mật khẩu", type="password")
            submitted = st.form_submit_button("Đăng nhập", use_container_width=True)
            
            if submitted:
                user_info = USERS_DB.get(username)
                if user_info and user_info["password"] == password:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    st.session_state["fullname"] = user_info["name"]
                    st.session_state["role"] = user_info["role"]
                    st.session_state["session_id"] = str(uuid.uuid4())
                    st.session_state["messages"] = []
                    st.rerun()
                else:
                    st.error("Sai tài khoản hoặc mật khẩu!")
    st.stop()

# --- 3. LẤY AGENT QUA PYTHON SINGLETON ---
agent = get_global_agent()

with st.sidebar:
    st.markdown("<h2 style='margin-top: -20px;'>✨ Reiner</h2>", unsafe_allow_html=True)
    
    st.markdown(f"**👤 {st.session_state['fullname']}**")
    st.caption(f"Quyền: {st.session_state['role'].upper()}")
    
    st.markdown("---")
    
    # Ô nhập API Key
    user_api_key = st.text_input(
        "🔑 Gemini API Key",
        value="",
        type="password",
        placeholder="Dán API Key vào đây rồi nhấn Enter..."
    )
    
    if not user_api_key:
        st.caption("⚠️ *Hãy nhập API Key ở trên để bắt đầu chat.*")
    else:
        st.caption("✅ *Đã nhận API Key.*")
    
    # Nút New chat
    if st.button("✨ Cuộc trò chuyện mới (New Chat)", use_container_width=True):
        st.session_state["messages"] = []
        st.session_state["session_id"] = str(uuid.uuid4())
        st.rerun()
    
    st.markdown("---")
    st.markdown("📂 **Lịch sử từ MinIO Datalake**")
    
    if st.button("🔄 Làm mới danh sách", use_container_width=True):
        st.rerun()
        
    # Lấy danh sách session từ MinIO local
    saved_sessions = fetch_all_sessions()
    
    if saved_sessions:
        selected_session = st.selectbox(
            "Chọn phiên chat cũ:",
            options=["-- Chọn phiên --"] + saved_sessions
        )
        
        if selected_session != "-- Chọn phiên --":
            if st.button("📥 Tải lịch sử phiên này", use_container_width=True):
                st.session_state["session_id"] = selected_session
                # Query và tải nội dung chat từ MinIO về lại màn hình
                loaded_logs = load_messages_by_session(selected_session)
                st.session_state["messages"] = loaded_logs
                st.success(f"Đã tải thành công phiên chat!")
                st.rerun()
    else:
        st.caption("Chưa có lịch sử lưu trữ nào trên MinIO.")
    
    st.markdown("---")
    st.markdown("🖼️ Images")
    
    if st.session_state["role"] == "admin":
        st.markdown("---")
        st.markdown("🔒 **Admin Panel**")
        st.markdown("⚙️ Quản lý Users")
        st.markdown("📊 Báo cáo Datalake MinIO")

    st.markdown("---")
    if st.button("🚪 Đăng xuất", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# --- 4. KHU VỰC CHAT ---
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if not st.session_state["messages"]:
    st.markdown(f"<h1 style='text-align: center; margin-top: 50px;'>✨ Xin chào {st.session_state['fullname']}</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: gray; font-weight: normal;'>Tôi là Reiner, hôm nay tôi có thể giúp gì cho bạn?</h3>", unsafe_allow_html=True)

for message in st.session_state["messages"]:
    role_raw = message.get("role", "user")
    safe_role = "user" if role_raw == "user" else "assistant"
    with st.chat_message(safe_role):
        st.markdown(str(message.get("content", "")))

if prompt := st.chat_input("Hỏi Reiner bất cứ điều gì..."):
    with st.chat_message("user"):
        st.markdown(prompt)

    previous_history = list(st.session_state["messages"])
    st.session_state["messages"].append({"role": "user", "content": prompt, "timestamp": datetime.now().isoformat()})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("Đang suy nghĩ..."):
            response = agent.chat_stream(
                user_message=prompt,
                history=previous_history,
                session_id=st.session_state["session_id"],
                username=st.session_state["username"],
                api_key_override=user_api_key
            )
        reply_text = str(response["reply"]) if "reply" in response else "Lỗi xử lý."
        message_placeholder.markdown(reply_text)
        
    st.session_state["messages"].append({"role": "assistant", "content": reply_text, "timestamp": datetime.now().isoformat()})