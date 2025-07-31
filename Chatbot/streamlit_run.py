import streamlit as st
import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import time
import json

load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:8000")  # Add default fallback


# Helper function to safely get JSON response
def safe_json_response(response):
    """Safely extract JSON from response with error handling"""
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        # If JSON decode fails, return error info based on status code
        if response.status_code == 404:
            return {"detail": "API endpoint not found. Check your API_URL."}
        elif response.status_code == 500:
            return {"detail": "Internal server error. Check if your API server is running."}
        elif response.status_code == 422:
            return {"detail": "Invalid request format."}
        else:
            return {"detail": f"Server error (Status: {response.status_code}). Response: {response.text[:100]}"}


# Helper function to make API requests with error handling
def make_api_request(method, url, **kwargs):
    """Make API request with comprehensive error handling"""
    try:
        response = requests.request(method, url, timeout=30, **kwargs)
        return response, None
    except requests.exceptions.ConnectionError:
        return None, "❌ Cannot connect to API server. Please check if the server is running."
    except requests.exceptions.Timeout:
        return None, "❌ Request timed out. The server might be overloaded."
    except requests.exceptions.RequestException as e:
        return None, f"❌ Request failed: {str(e)}"


# 🎨 Page configuration
st.set_page_config(
    page_title="AI Q&A Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🎨 Custom CSS for ultra-cool styling with glow effects
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;500;600;700&display=swap');

    /* Dark cyberpunk background */
    .stApp {
        background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 25%, #16213e 50%, #0f3460 75%, #000000 100%);
        background-attachment: fixed;
    }

    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: 
            radial-gradient(circle at 20% 20%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(255, 119, 198, 0.3) 0%, transparent 50%),
            radial-gradient(circle at 40% 40%, rgba(120, 219, 255, 0.2) 0%, transparent 50%);
        pointer-events: none;
        z-index: -1;
    }

    .main {
        padding-top: 2rem;
        color: #ffffff;
    }

    /* Animated title with neon glow */
    .neon-title {
        font-family: 'Orbitron', monospace;
        text-align: center;
        font-size: 4rem;
        font-weight: 900;
        background: linear-gradient(45deg, #00ffff, #ff00ff, #ffff00, #00ffff);
        background-size: 400% 400%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: neon-glow 3s ease-in-out infinite alternate, gradient-shift 4s ease-in-out infinite;
        text-shadow: 
            0 0 10px rgba(0, 255, 255, 0.5),
            0 0 20px rgba(0, 255, 255, 0.3),
            0 0 30px rgba(0, 255, 255, 0.1);
        margin-bottom: 1rem;
    }

    @keyframes neon-glow {
        from {
            text-shadow: 
                0 0 10px rgba(0, 255, 255, 0.5),
                0 0 20px rgba(0, 255, 255, 0.3),
                0 0 30px rgba(0, 255, 255, 0.1);
        }
        to {
            text-shadow: 
                0 0 20px rgba(255, 0, 255, 0.8),
                0 0 30px rgba(255, 0, 255, 0.5),
                0 0 40px rgba(255, 0, 255, 0.3);
        }
    }

    @keyframes gradient-shift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Login container with glassmorphism and glow */
    .login-container {
        max-width: 450px;
        margin: 2rem auto;
        padding: 2.5rem;
        border-radius: 20px;
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.3),
            0 0 0 1px rgba(255, 255, 255, 0.05);
        position: relative;
        overflow: hidden;
    }

    .login-container::before {
        content: '';
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        background: linear-gradient(45deg, #00ffff, #ff00ff, #ffff00, #00ffff);
        background-size: 400% 400%;
        border-radius: 22px;
        z-index: -1;
        animation: border-glow 3s ease-in-out infinite;
        opacity: 0.6;
    }

    @keyframes border-glow {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }

    /* Success glow animation */
    .success-glow {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: radial-gradient(circle, rgba(0, 255, 127, 0.3) 0%, transparent 70%);
        animation: success-pulse 2s ease-out;
        pointer-events: none;
        z-index: 1000;
    }

    @keyframes success-pulse {
        0% { opacity: 0; transform: scale(0.8); }
        50% { opacity: 1; transform: scale(1.1); }
        100% { opacity: 0; transform: scale(1.3); }
    }

    /* Chat messages with cyberpunk styling */
    .chat-message {
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 15px;
        position: relative;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
    }

    .chat-message:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
    }

    .question {
        background: linear-gradient(135deg, rgba(0, 123, 255, 0.2), rgba(0, 255, 255, 0.1));
        border-left: 4px solid #00ffff;
        box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
    }

    .answer {
        background: linear-gradient(135deg, rgba(255, 0, 255, 0.2), rgba(138, 43, 226, 0.1));
        border-left: 4px solid #ff00ff;
        box-shadow: 0 0 20px rgba(255, 0, 255, 0.2);
    }

    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, rgba(0, 0, 0, 0.8), rgba(26, 26, 46, 0.9));
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Status badge with pulse animation */
    .status-badge {
        display: inline-block;
        padding: 0.4rem 0.8rem;
        border-radius: 25px;
        font-size: 0.9rem;
        font-weight: 600;
        color: #000;
        background: linear-gradient(45deg, #00ff88, #00ccff);
        box-shadow: 0 0 15px rgba(0, 255, 136, 0.5);
        animation: pulse-glow 2s ease-in-out infinite alternate;
        font-family: 'Rajdhani', sans-serif;
    }

    @keyframes pulse-glow {
        from { box-shadow: 0 0 15px rgba(0, 255, 136, 0.5); }
        to { box-shadow: 0 0 25px rgba(0, 255, 136, 0.8); }
    }

    /* Button enhancements */
    .stButton > button {
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        font-family: 'Rajdhani', sans-serif;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        background: linear-gradient(45deg, #764ba2 0%, #667eea 100%);
    }

    /* Text inputs with glow */
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 10px;
        color: #ffffff;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }

    .stTextInput > div > div > input:focus {
        border: 1px solid #00ffff;
        box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
        background: rgba(255, 255, 255, 0.08);
    }

    /* Selectbox styling */
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 10px;
        backdrop-filter: blur(10px);
    }

    /* Spinner customization */
    .stSpinner > div {
        border-top-color: #00ffff !important;
        border-right-color: #ff00ff !important;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }

    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        color: #ffffff;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(45deg, #00ffff, #ff00ff);
        color: #000;
        font-weight: 600;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb {
        background: linear-gradient(45deg, #00ffff, #ff00ff);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(45deg, #ff00ff, #00ffff);
    }

    /* Error styling */
    .error-container {
        background: rgba(255, 0, 0, 0.1);
        border: 1px solid rgba(255, 0, 0, 0.3);
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 🎨 Title with epic neon effect
st.markdown("""
<div style="text-align: center; margin-bottom: 3rem;">
    <h1 class="neon-title">🤖 AI Q&A</h1>
    <p style="color: #00ffff; font-size: 1.4rem; margin-top: 1rem; font-family: 'Rajdhani', sans-serif; font-weight: 300; text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);">
        ⚡ A Chatbot to answer all your questions. ⚡
    </p>
</div>

<script>
function showSuccessGlow() {
    const glowDiv = document.createElement('div');
    glowDiv.className = 'success-glow';
    document.body.appendChild(glowDiv);
    setTimeout(() => {
        document.body.removeChild(glowDiv);
    }, 2000);
}
</script>
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
if "random_query" not in st.session_state:
    st.session_state.random_query = ""
if "clear_input" not in st.session_state:
    st.session_state.clear_input = False

# ✅ If not logged in: show Register/Login
if st.session_state.access_token is None:
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)

        st.markdown("### 🔐 USER LOGIN")
        st.markdown("🌌 Please login to continue")

        # Create tabs for Login and Register
        tab1, tab2 = st.tabs(["🔑 LOGIN", "📝 REGISTER"])

        with tab1:
            st.markdown("##### 🔑 Login to your account")
            login_username = st.text_input("Username", key="login_user", placeholder="Enter your username")
            login_password = st.text_input("Password", type="password", key="login_pass",
                                           placeholder="Enter your password")

            col_login1, col_login2 = st.columns(2)
            with col_login2:
                if st.button("🚀 LOGIN", type="primary", use_container_width=True):
                    if login_username and login_password:
                        with st.spinner("🔄 Logging in..."):
                            res, error = make_api_request(
                                "POST",
                                f"{API_URL}/token",
                                data={"username": login_username, "password": login_password},
                                headers={"Content-Type": "application/x-www-form-urlencoded"}
                            )

                        if error:
                            st.error(error)
                        elif res and res.status_code == 200:
                            response_data = safe_json_response(res)
                            if "access_token" in response_data:
                                st.session_state.access_token = response_data["access_token"]
                                st.session_state.username = login_username
                                # Show epic success animation
                                st.markdown("""
                                <div class="success-glow"></div>
                                <script>
                                    const successDiv = document.querySelector('.success-glow');
                                    if (successDiv) {
                                        successDiv.style.display = 'block';
                                }
                                </script>
                                """, unsafe_allow_html=True)
                                st.success("✅ Login successful! Welcome...")
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error("❌ Invalid response from server")
                        else:
                            response_data = safe_json_response(res)
                            st.error(f"❌ {response_data.get('detail', 'Login failed.')}")
                    else:
                        st.warning("⚠️ Please enter username and password")

        with tab2:
            st.markdown("##### 📝 Create new account")
            reg_username = st.text_input("Username", key="reg_user", placeholder="Choose your username")
            reg_password = st.text_input("Password", type="password", key="reg_pass",
                                         placeholder="Set your password")

            col_reg1, col_reg2 = st.columns(2)
            with col_reg2:
                if st.button("📝 REGISTER", type="secondary", use_container_width=True):
                    if reg_username and reg_password:
                        with st.spinner("🧬 Creating account..."):
                            res, error = make_api_request(
                                "POST",
                                f"{API_URL}/register",
                                json={"username": reg_username, "password": reg_password}
                            )

                        if error:
                            st.error(error)
                        elif res and res.status_code == 200:
                            response_data = safe_json_response(res)
                            # Show epic success animation
                            st.markdown("""
                            <div class="success-glow"></div>
                            <script>
                                const successDiv = document.querySelector('.success-glow');
                                if (successDiv) {
                                    successDiv.style.display = 'block';
                                }
                            </script>
                            """, unsafe_allow_html=True)
                            st.success(
                                f"✅ {response_data.get('message', 'Registration successful')} 🧠 Account created!")
                            st.info("🔄 Switch to LOGIN tab to sign in")
                        else:
                            response_data = safe_json_response(res)
                            st.error(f"❌ {response_data.get('detail', 'Registration failed.')}")
                    else:
                        st.warning("⚠️ Please enter username and password")

        st.markdown('</div>', unsafe_allow_html=True)

    st.stop()

# ✅ Sidebar for logged-in users
with st.sidebar:
    st.markdown("### 🧠 USER PANEL")
    st.markdown(f'<span class="status-badge">🔥 ONLINE</span> **{st.session_state.username}**', unsafe_allow_html=True)

    st.markdown("---")

    # Model selection with cyberpunk styling
    st.markdown("### ⚡ AI MODEL")
    engine = st.selectbox(
        "Choose your AI model:",
        [
            "🚀 gemini-2.5-flash-lite-preview-06-17",
            "🧠 llama3-8b-8192",
            "💎 gemma2-9b-it",
            "⚡ llama-3.1-8b-instant",
#            "🔬 llama3.2:latest",
#            "📱 gemma3:1b"
        ],
        help="Each AI model has unique capabilities and response patterns",
        format_func=lambda x: x.split(' ', 1)[1] if ' ' in x else x
    )

    st.markdown("---")

    # Action buttons with enhanced styling
    st.markdown("### 🛠️ ACTIONS")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📚 HISTORY", use_container_width=True):
            st.session_state.show_history = not st.session_state.show_history

    with col2:
        if st.button("🗑️ CLEAR", use_container_width=True):
            headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
            res, error = make_api_request("DELETE", f"{API_URL}/history", headers=headers)

            if error:
                st.error(error)
            elif res and res.status_code == 200:
                st.success("✅ History cleared!")
                st.session_state.chat_messages = []
            else:
                st.error(f"❌ Clear failed (Status: {res.status_code if res else 'Unknown'})")

    if st.button("🚪 LOGOUT", type="secondary", use_container_width=True):
        st.session_state.access_token = None
        st.session_state.username = None
        st.session_state.chat_messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("### 🔮 MODEL INFO")
    core_info = {
        "🚀 gemini-2.5-flash-lite-preview-06-17": "⚡ Fast Responses",
        "🧠 llama3-8b-8192": "🎯 Balanced",
        "💎 gemma2-9b-it": "🌟 Creative",
        "⚡ llama-3.1-8b-instant": "🔥 Quick",
        "🔬 llama3.2:latest": "🧪 Latest",
        "📱 gemma3:1b": "💫 Compact"
    }
    selected_core = next((k for k in core_info.keys() if engine in k), None)
    if selected_core:
        st.info(f"{core_info[selected_core]}")

    # Add some activity visualization
    st.markdown("---")
    st.markdown("### 🌐 STATUS")
    st.markdown("""
    <div style="text-align: center;">
        <div style="color: #00ffff; font-size: 0.8rem; animation: pulse-glow 2s infinite;">
            ████ CHATBOT ACTIVE ████<br>
            ◦◉◦◉◦◉◦◉◦◉◦◉◦◉◦<br>
            STATUS: READY
        </div>
    </div>
    """, unsafe_allow_html=True)

# ✅ Main chat interface
st.markdown("### 🚀 CHAT INTERFACE")

# Handle random query generation first
if st.session_state.get("generate_random", False):
    random_queries = [
        "What is the meaning of consciousness?",
        "How does artificial intelligence work?",
        "What are the implications of quantum computing?",
        "Explain the concept of neural networks",
        "What is the future of human-AI interaction?",
        "How does machine learning differ from traditional programming?",
        "What are the ethical considerations in AI development?",
        "Describe the relationship between data and intelligence"
    ]
    import random

    st.session_state.random_query = random.choice(random_queries)
    st.session_state.generate_random = False
    st.rerun()

# Handle input clearing
input_value = ""
if st.session_state.clear_input:
    input_value = ""
    st.session_state.clear_input = False
elif st.session_state.random_query:
    input_value = st.session_state.random_query
    st.session_state.random_query = ""

# Chat input with cyberpunk styling
with st.container():
    user_input = st.text_input(
        "Send your question to the AI:",
        placeholder="Ask anything...",
        key="chat_input",
        label_visibility="collapsed",
        value=input_value
    )

    col1, col2, col3 = st.columns([6, 1, 1])
    with col2:
        send_button = st.button("🚀 SEND", type="primary")
    with col3:
        random_button = st.button("🎲 RANDOM", help="Generate a random question")

# Random query generation
if random_button:
    st.session_state.generate_random = True
    st.rerun()

# Process user input
if user_input and send_button:
    engine_name = engine.split(' ', 1)[1] if ' ' in engine else engine
    with st.spinner(f"🧠 Processing with {engine_name}..."):
        payload = {"question": user_input, "engine": engine_name}
        headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
        res, error = make_api_request("POST", f"{API_URL}/ask", json=payload, headers=headers)

    if error:
        st.error(error)
    elif res and res.status_code == 200:
        response_data = safe_json_response(res)
        if "answer" in response_data:
            answer = response_data['answer']
            timestamp = datetime.now().strftime("%H:%M:%S")

            # Add to session messages
            st.session_state.chat_messages.append({
                "question": user_input,
                "answer": answer,
                "timestamp": timestamp,
                "engine": engine
            })

            # Clear input and rerun
            st.session_state.clear_input = True
            st.rerun()
        else:
            st.error("❌ Invalid response format from server")
    else:
        response_data = safe_json_response(res)
        st.error(f"❌ Request failed: {response_data.get('detail', 'Unknown error')}")

# Display recent chat messages
if st.session_state.chat_messages:
    st.markdown("### 🧠 RECENT CONVERSATIONS")

    # Show last 3 messages
    for i, msg in enumerate(reversed(st.session_state.chat_messages[-3:])):
        with st.container():
            st.markdown(f"""
            <div class="chat-message question">
                <strong>🤖 YOUR QUESTION:</strong> {msg['question']}
                <br><small>⚡ {msg['timestamp']} | 🔮 {msg['engine'].split(' ', 1)[1] if ' ' in msg['engine'] else msg['engine']}</small>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="chat-message answer">
                <strong>🧠 AI RESPONSE:</strong> {msg['answer']}
            </div>
            """, unsafe_allow_html=True)

            if i < len(st.session_state.chat_messages[-3:]) - 1:
                st.markdown('<div style="border-top: 1px solid rgba(255,255,255,0.1); margin: 1rem 0;"></div>',
                            unsafe_allow_html=True)

# ✅ Show full chat history if toggled
if st.session_state.show_history:
    st.markdown('<div style="border-top: 2px solid rgba(0,255,255,0.5); margin: 2rem 0;"></div>',
                unsafe_allow_html=True)
    st.markdown("### 📚 COMPLETE CHAT HISTORY")

    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    res, error = make_api_request("GET", f"{API_URL}/history", headers=headers)

    if error:
        st.error(error)
    elif res and res.status_code == 200:
        response_data = safe_json_response(res)
        history = response_data if isinstance(response_data, list) else []

        if history:
            for i, chat in enumerate(history):
                with st.expander(
                        f"🧠 Chat {len(history) - i} - {chat.get('created_at', 'Timestamp Unknown')}"):
                    st.markdown(f"**🤖 YOUR QUESTION:** {chat.get('question', 'N/A')}")
                    st.markdown(f"**🧠 AI RESPONSE:** {chat.get('answer', 'N/A')}")
                    if 'created_at' in chat:
                        st.caption(f"⚡ Time: {chat['created_at']}")
        else:
            st.info("🌌 No chat history found. Start asking questions!")
    else:
        response_data = safe_json_response(res)
        st.error(f"❌ Unable to load history: {response_data.get('detail', 'Unknown error')}")

# Cyberpunk footer
st.markdown('<div style="border-top: 2px solid rgba(0,255,255,0.3); margin: 3rem 0 1rem 0;"></div>',
            unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; color: #00ffff; padding: 2rem; font-family: 'Orbitron', monospace;">
    <div style="font-size: 1.2rem; margin-bottom: 0.5rem; text-shadow: 0 0 10px rgba(0,255,255,0.5);">
        ⚡ AI CHATBOT ACTIVE ⚡
    </div>
    <div style="font-size: 0.9rem; opacity: 0.8;">
        🔒 Secure Chat • 🤖 AI Models • 💬 Real-Time Responses
    </div>
    <div style="margin-top: 1rem; font-size: 0.7rem; color: #ff00ff;">
        [ CHATBOT STATUS: FULLY OPERATIONAL ]
    </div>
</div>
""", unsafe_allow_html=True)