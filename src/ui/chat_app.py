import streamlit as st
from src.core.agent_orchestrator import EnterpriseAIAgent

# 1. Cấu hình trang cơ bản
st.set_page_config(page_title="Reiner AI", page_icon="✨", layout="wide")

# Xóa các khoảng trắng mặc định của Streamlit để giao diện tràn viền giống Gemini hơn
st.markdown("""
    <style>
        .block-container { padding-top: 2rem; padding-bottom: 0rem; }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Khởi tạo Agent (API Key và Model đã được cấu hình ngầm trong agent_orchestrator)
@st.cache_resource
def get_agent():
    return EnterpriseAIAgent()

agent = get_agent()

# ==========================================
# 2. XÂY DỰNG SIDEBAR (THEO PHONG CÁCH GEMINI)
# ==========================================
with st.sidebar:
    # Header với Tên và Icon
    st.markdown("<h2 style='display: flex; align-items: center; gap: 8px; margin-top: -20px;'>✨ Reiner</h2>", unsafe_allow_html=True)
    
    # Nút New Chat
    if st.button("📝 New chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Các menu điều hướng tĩnh (Mô phỏng giao diện)
    st.markdown("📂 Library")
    st.markdown("🖼️ Images")
    st.markdown("🕒 Scheduled")
    st.markdown("🎓 Students")
    st.markdown("••• More")
    
    st.markdown("---")
    
    # Khu vực Notebooks
    st.markdown("<p style='color: gray; font-size: 14px; margin-bottom: 5px;'>Notebooks</p>", unsafe_allow_html=True)
    st.markdown("➕ New notebook")
    st.markdown("📄 Untitled notebook")
    st.markdown("📄 C Language Input, Output, and Fo...")
    
    st.markdown("---")
    
    # Khu vực Lịch sử trò chuyện
    st.markdown("<div style='display: flex; justify-content: space-between; align-items: center;'><p style='color: gray; font-size: 14px; margin-bottom: 5px;'>All</p><span>▽</span></div>", unsafe_allow_html=True)
    st.markdown("💬 Tiếp tục triển khai AI Streamlit")
    st.markdown("💬 Thuật toán Random Forest")
    st.markdown("💬 Tư vấn chọn quần mới")
    st.markdown("💬 Hỗ trợ Giải Bài Toán")
    st.markdown("💬 Cận thị 1.25 độ có phải đi nghĩa vụ...")
    st.markdown("💬 Xử lý sau khi đăng nhập")


# ==========================================
# 3. KHU VỰC CHAT CHÍNH (MAIN AREA)
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# Chỉ hiển thị lời chào nếu chưa có tin nhắn nào
if not st.session_state.messages:
    st.markdown("<h1 style='text-align: center; margin-top: 50px;'>✨ Xin chào, tôi là Reiner</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: gray; font-weight: normal;'>Hôm nay tôi có thể giúp gì cho bạn?</h3>", unsafe_allow_html=True)

# Hiển thị lịch sử tin nhắn
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Khung nhập liệu (Chat input)
if prompt := st.chat_input("Hỏi Reiner bất cứ điều gì..."):
    # Hiển thị tin nhắn của người dùng
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # AI xử lý và phản hồi
    with st.chat_message("model"):
        message_placeholder = st.empty()
        
        with st.spinner("Đang suy nghĩ..."):
            # Gọi Agent. Không cần truyền API key hay Model nữa vì đã fix cứng ở backend
            response = agent.chat_stream(
                user_message=prompt,
                history=st.session_state.messages
            )
            
        reply_text = response.get("reply", "Xin lỗi, đã có lỗi xảy ra trong quá trình xử lý.")
        message_placeholder.markdown(reply_text)
        
    # Lưu tin nhắn của AI vào lịch sử
    st.session_state.messages.append({"role": "model", "content": reply_text})