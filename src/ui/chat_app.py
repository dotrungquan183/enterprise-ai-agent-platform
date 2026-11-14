import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
from src.core.agent_orchestrator import EnterpriseAIAgent

st.set_page_config(
    page_title="Gemini-Style AI Agent (LLM + ML Tools + RAG)",
    page_icon="✨",
    layout="wide"
)

@st.cache_resource
def get_agent():
    return EnterpriseAIAgent()

agent = get_agent()

# --- THANH BÊN (SIDEBAR) ---
with st.sidebar:
    st.title("✨ Cấu hình Bộ não AI")
    st.caption("Kết nối LLM thực thụ để mở khóa khả năng suy luận đa lượt & tự động gọi hàm (Function Calling).")

    provider = st.selectbox(
        "1. Chọn Nhà cung cấp LLM:",
        ["gemini", "groq", "openai", "ollama"],
        index=0,
        help="Khuyên dùng 'gemini' (Miễn phí qua Google AI Studio) hoặc 'groq' (Miễn phí Llama-3.3-70B)."
    )

    model_map = {
        "gemini": ["gemini-3.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"],
        "groq": ["llama-3.3-70b-versatile", "qwen-qwq-32b"],
        "openai": ["gpt-4o-mini", "gpt-4o"],
        "ollama": ["qwen2.5:7b", "llama3.1:8b", "deepseek-r1:7b"]
    }
    model_name = st.selectbox("2. Chọn Mô hình (Model):", model_map[provider])

    api_key = ""
    if provider != "ollama":
        api_key = st.text_input(
            f"3. Nhập {provider.upper()} API Key:",
            type="password",
            help="Lấy Gemini API Key miễn phí tại: https://aistudio.google.com/apikey"
        )
        if not api_key:
            st.warning("💡 Hãy nhập API Key (Miễn phí tại aistudio.google.com) để con AI thông minh như Gemini thật!")
        else:
            st.success("✅ Đã kết nối API Key! AI Agent đã sẵn sàng suy luận tự do.")

    st.divider()
    st.subheader("🧪 Prompt Thử nghiệm Đẳng cấp")
    p1 = st.button("🔍 Phân tích CUST_001 & đề xuất chiến lược giữ chân")
    p2 = st.button("⚖️ So sánh CUST_001 và CUST_002 rồi viết báo cáo")
    p3 = st.button("🛒 Tư vấn combo khi khách mua Laptop (FP-Growth)")
    p4 = st.button("📐 Giải thích toán học PCA & thử gọi ML Tool")

    if st.button("🗑️ Xóa lịch sử trò chuyện", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- MÀN HÌNH CHAT CHÍNH ---
st.title("✨ Enterprise AI Collaborator (Agentic LLM + 12 ML Tools + RAG)")
st.markdown(
    "Mô phỏng kiến trúc **Gemini / ChatGPT thực thụ**: Tự động suy luận, nhớ ngữ cảnh hội thoại nhiều lượt, "
    "hỗ trợ công thức Toán LaTeX và **tự động kích hoạt các mô hình Machine Learning** khi cần số liệu thực tế."
)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Xin chào! Tôi là **AI Collaborator** của bạn.\n\n"
                "Sau khi bạn điền **Gemini API Key** (hoặc Groq/OpenAI/Ollama) ở thanh bên trái, bạn có thể:\n"
                "- Trò chuyện tự do mọi chủ đề, yêu cầu chứng minh công thức Toán học (LaTeX), viết code Python/SQL.\n"
                "- Bảo tôi phân tích dữ liệu khách hàng thực tế (VD: *\"So sánh rủi ro rời bỏ của CUST_001 và CUST_002\"*) — "
                "tôi sẽ **tự động gọi mô hình Random Forest, K-Means, PCA, Linear Ridge** ở dưới ngầm để lấy số liệu phân tích cho bạn!"
            )
        }
    ]

# Hiển thị toàn bộ lịch sử trò chuyện
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("tools_called"):
            with st.expander(f"🛠️ Đã tự động kích hoạt {len(msg['tools_called'])} ML/RAG Tool(s)", expanded=False):
                st.json(msg["tools_called"])
        st.markdown(msg["content"])

# Xử lý câu hỏi từ nút bấm hoặc ô nhập
preset_prompt = None
if p1:
    preset_prompt = "Hãy phân tích toàn diện khách hàng CUST_001 bằng mô hình ML, đối chiếu với chính sách nội bộ xem họ thuộc nhóm nào và đề xuất phương án giữ chân cụ thể."
elif p2:
    preset_prompt = "Hãy kiểm tra cả hai khách hàng CUST_001 và CUST_002, lập bảng so sánh các chỉ số dự báo ML (cụm K-Means, CLV, xác suất rời bỏ Random Forest) giữa hai người này."
elif p3:
    preset_prompt = "Khách hàng vừa bỏ Laptop vào giỏ hàng. Hãy chạy thuật toán FP-Growth xem nên gợi ý mua kèm món gì và viết một lời chào mời khéo léo gửi cho khách."
elif p4:
    preset_prompt = "Giải thích ngắn gọn bản chất toán học của PCA bằng công thức LaTeX, sau đó gọi thử công cụ phân tích khách hàng CUST_003 để xem tọa độ nén PCA 2D thực tế của họ là bao nhiêu."

user_query = st.chat_input("Hỏi bất cứ điều gì (Toán học, Code, LaTeX, hoặc phân tích khách hàng CUST_001, giỏ hàng...)")
active_query = preset_prompt or user_query

if active_query:
    # Lưu lịch sử trước khi thêm câu mới để truyền vào bộ nhớ Agent
    prior_history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]

    st.session_state.messages.append({"role": "user", "content": active_query})
    with st.chat_message("user"):
        st.markdown(active_query)

    with st.chat_message("assistant"):
        with st.status("🧠 AI đang suy luận & kiểm tra bộ công cụ Machine Learning...", expanded=True) as status:
            st.write("Đang phân tích ngữ cảnh hội thoại và quyết định Tool Calling...")
            result = agent.chat_stream(
                user_message=active_query,
                history=prior_history,
                provider=provider,
                api_key=api_key,
                model_name=model_name
            )
            tools_used = result.get("tools_called", [])
            if tools_used:
                st.write(f"✅ Đã tự động gọi **{len(tools_used)} công cụ ML/RAG**: `{[t['tool_name'] for t in tools_used]}`")
            else:
                st.write("✅ Trả lời trực tiếp từ tri thức LLM (Không cần gọi Tool)")
            status.update(label=f"✨ Hoàn tất ({result['engine_used']})", state="complete", expanded=False)

        if tools_used:
            with st.expander(f"🛠️ Chi tiết các hàm ML/RAG mà AI đã tự động gọi ({len(tools_used)})", expanded=False):
                st.json(tools_used)

        # Hiệu ứng gõ chữ Streaming mượt mà như Gemini/ChatGPT
        def stream_generator(text: str):
            for word in text.split(" "):
                yield word + " "
                time.sleep(0.012)

        st.write_stream(stream_generator(result["reply"]))

    st.session_state.messages.append({
        "role": "assistant",
        "content": result["reply"],
        "tools_called": tools_used
    })
    if preset_prompt:
        st.rerun()
