import streamlit as st
import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import time

load_dotenv()
API_URL = os.getenv("API_URL")

# 🎨 Page configuration
st.set_page_config(
    page_title="AI Q&A Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🎨 Custom CSS for better styling
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }

    .stTitle {
        text-align: center;
        color: #1f77b4;
        font-size: 3rem !important;
        margin-bottom: 2rem;
    }

    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        background-color: #f8f9fa;
    }

    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        background-color: #f0f2f6;
    }

    .question {
        background-color: #e3f2fd;
        border-left-color: #2196f3;
    }

    .answer {
        background-color: #f3e5f5;
        border-left-color: #9c27b0;
    }

    .sidebar .stSelectbox {
        margin-bottom: 1rem;
    }

    .metric-container {
        display: flex;
        justify-content: space-around;
        margin: 1rem 0;
    }

    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        color: white;
        background-color: #28a745;
    }
</style>
""", unsafe_allow_html=True)

# 🎨 Title with gradient effect
st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <h1 style="background: linear-gradient(90deg, #1f77b4, #ff7f0e, #2ca02c); 
               -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
               font-size: 3rem; margin: 0;">
        🤖 AI Q&A Chatbot
    </h1>
    <p style="color: #666; font-size: 1.2rem; margin-top: 0.5rem;">
        Secure conversations powered by advanced AI models
    </p>
</div>
""", unsafe_allow_html=True)

# ✅ Initialize session state keys
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "show_history" not in st.session_state:
    st.session_state.show_history = False
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# ✅ If not logged in: show Register/Login
if st.session_state.access_token is None:
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)

        st.markdown("### 🔐 Welcome Back!")
        st.markdown("Please login or create a new account to continue")

        # Create tabs for Login and Register
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])

        with tab1:
            st.markdown("##### Login to your account")
            login_username = st.text_input("Username", key="login_user", placeholder="Enter your username")
            login_password = st.text_input("Password", type="password", key="login_pass",
                                           placeholder="Enter your password")

            col_login1, col_login2 = st.columns(2)
            with col_login2:
                if st.button("🚀 Login", type="primary", use_container_width=True):
                    if login_username and login_password:
                        with st.spinner("Logging in..."):
                            res = requests.post(
                                f"{API_URL}/token",
                                data={"username": login_username, "password": login_password},
                                headers={"Content-Type": "application/x-www-form-urlencoded"}
                            )
                        if res.status_code == 200:
                            st.session_state.access_token = res.json()["access_token"]
                            st.session_state.username = login_username
                            st.success("✅ Login successful!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ {res.json().get('detail', 'Login failed.')}")
                    else:
                        st.warning("Please fill in all fields")

        with tab2:
            st.markdown("##### Create a new account")
            reg_username = st.text_input("Username", key="reg_user", placeholder="Choose a username")
            reg_password = st.text_input("Password", type="password", key="reg_pass",
                                         placeholder="Choose a secure password")

            col_reg1, col_reg2 = st.columns(2)
            with col_reg2:
                if st.button("📝 Register", type="secondary", use_container_width=True):
                    if reg_username and reg_password:
                        with st.spinner("Creating account..."):
                            res = requests.post(f"{API_URL}/register",
                                                json={"username": reg_username, "password": reg_password})
                        if res.status_code == 200:
                            st.success(f"✅ {res.json()['message']}")
                            st.info("Please switch to the Login tab to sign in")
                        else:
                            st.error(f"❌ {res.json().get('detail', 'Registration failed.')}")
                    else:
                        st.warning("Please fill in all fields")

        st.markdown('</div>', unsafe_allow_html=True)

    st.stop()

# ✅ Sidebar for logged-in users
with st.sidebar:
    st.markdown("### 👤 User Panel")
    st.markdown(f'<span class="status-badge">🟢 Online</span> **{st.session_state.username}**', unsafe_allow_html=True)

    st.markdown("---")

    # Model selection with better styling
    st.markdown("### 🎯 AI Model Selection")
    engine = st.selectbox(
        "Choose your AI model:",
        [
            "gemini-2.5-flash-lite-preview-06-17",
            "llama3-8b-8192",
            "gemma2-9b-it",
            "llama-3.1-8b-instant",
            "llama3.2:latest",
            "gemma3:1b"
        ],
        help="Different models have varying capabilities and response styles"
    )

    st.markdown("---")

    # Action buttons
    st.markdown("### 🛠️ Actions")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📚 History", use_container_width=True):
            st.session_state.show_history = not st.session_state.show_history

    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
            res = requests.delete(f"{API_URL}/history", headers=headers)
            if res.status_code == 200:
                st.success("✅ History cleared!")
                st.session_state.chat_messages = []
            else:
                st.error("❌ Failed to clear")

    if st.button("🚪 Logout", type="secondary", use_container_width=True):
        st.session_state.access_token = None
        st.session_state.username = None
        st.session_state.chat_messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("### ℹ️ Model Info")
    model_info = {
        "gemini-2.5-flash-lite-preview-06-17": "🚀 Fast & Efficient",
        "llama3-8b-8192": "🧠 Balanced Performance",
        "gemma2-9b-it": "💡 Creative Responses",
        "llama-3.1-8b-instant": "⚡ Ultra Fast",
        "llama3.2:latest": "🔬 Latest Features",
        "gemma3:1b": "📱 Lightweight"
    }
    st.info(model_info.get(engine, "AI Model"))

# ✅ Main chat interface
st.markdown("### 💬 Chat with AI")

# Chat input
with st.container():
    user_input = st.text_input(
        "Your question:",
        placeholder="Ask me anything...",
        key="chat_input",
        label_visibility="collapsed"
    )

    col1, col2, col3 = st.columns([6, 1, 1])
    with col2:
        send_button = st.button("📤 Send", type="primary")
    with col3:
        st.button("🎲 Random", help="Get a random question suggestion")

# Process user input
if user_input and send_button:
    with st.spinner(f"🤔 Thinking with {engine}..."):
        payload = {"question": user_input, "engine": engine}
        headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
        res = requests.post(f"{API_URL}/ask", json=payload, headers=headers)

    if res.status_code == 200:
        answer = res.json()['answer']
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Add to session messages
        st.session_state.chat_messages.append({
            "question": user_input,
            "answer": answer,
            "timestamp": timestamp,
            "engine": engine
        })

        st.rerun()
    else:
        st.error("❌ Failed to get answer. Please try again.")

# Display recent chat messages
if st.session_state.chat_messages:
    st.markdown("### 💭 Recent Conversation")

    # Show last 3 messages
    for i, msg in enumerate(reversed(st.session_state.chat_messages[-3:])):
        with st.container():
            st.markdown(f"""
            <div class="chat-message question">
                <strong>🤔 You:</strong> {msg['question']}
                <br><small>⏰ {msg['timestamp']} | 🤖 {msg['engine']}</small>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="chat-message answer">
                <strong>🤖 AI:</strong> {msg['answer']}
            </div>
            """, unsafe_allow_html=True)

            if i < len(st.session_state.chat_messages[-3:]) - 1:
                st.markdown("---")

# ✅ Show full chat history if toggled
if st.session_state.show_history:
    st.markdown("---")
    st.markdown("### 📚 Complete Chat History")

    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    res = requests.get(f"{API_URL}/history", headers=headers)

    if res.status_code == 200:
        history = res.json()
        if history:
            for i, chat in enumerate(history):
                with st.expander(f"💬 Conversation {len(history) - i} - {chat.get('created_at', 'Unknown time')}"):
                    st.markdown(f"**🤔 Question:** {chat['question']}")
                    st.markdown(f"**🤖 Answer:** {chat['answer']}")
                    if 'created_at' in chat:
                        st.caption(f"📅 {chat['created_at']}")
        else:
            st.info("📝 No chat history found. Start a conversation!")
    else:
        st.error("❌ Failed to load chat history.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <small>🔒 Secure conversations • 🤖 AI-powered responses • 💬 Real-time chat</small>
</div>
""", unsafe_allow_html=True)