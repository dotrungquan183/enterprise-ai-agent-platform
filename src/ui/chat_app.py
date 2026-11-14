import sys
import os

# --- FIX LỖI ĐƯỜNG DẪN IMPORT (No module named 'src') ---
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

import streamlit as st
import uuid
from src.core.agent_orchestrator import get_global_agent

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
    # Ô nhập API Key (đặt sẵn key mới của bạn làm giá trị mặc định)
    user_api_key = st.text_input(
        "🔑 Gemini API Key",
        value="AQ.Ab8RN6Jxm2JUUcnf3GSVAQZHqB-ggHb4qjfZDWDbSHNCYvyTsQ",
        type="password"
    )
    
    if st.button("📝 New chat", use_container_width=True):
        st.session_state["messages"] = []
        st.session_state["session_id"] = str(uuid.uuid4())
        st.rerun()
    
    st.markdown("---")
    st.markdown("📂 Library")
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
    safe_role = "user" if message["role"] == "user" else "assistant"
    with st.chat_message(safe_role):
        st.markdown(str(message["content"]))

if prompt := st.chat_input("Hỏi Reiner bất cứ điều gì..."):
    with st.chat_message("user"):
        st.markdown(prompt)

    previous_history = list(st.session_state["messages"])
    st.session_state["messages"].append({"role": "user", "content": prompt})

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
        
    st.session_state["messages"].append({"role": "assistant", "content": reply_text})