import streamlit as st
import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import time
import json

load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:8000")


# Helper function to safely get JSON response
def safe_json_response(response):
    """Safely extract JSON from response with error handling"""
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        if response.status_code == 404:
            return {"detail": "API endpoint not found. Check your API_URL."}
        elif response.status_code == 500:
            return {"detail": "Internal server error. Check if your API server is running."}
        elif response.status_code == 422:
            return {"detail": "Invalid request format."}
        else:
            return {"detail": f"Server error (Status: {response.status_code}). Response: {response.text[:100]}"}


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


# Page configuration and CSS
st.set_page_config(
    page_title="AI Q&A Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Complete Custom CSS for ultra-cool cyberpunk styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;500;600;700&display=swap');

    /* Dark cyberpunk background */
    .stApp {
        background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 25%, #16213e 50%, #0f3460 75%, #000000 100%);
        background-attachment: fixed;
    }

    /* Remove default Streamlit styling */
    .stApp > header {
        background-color: transparent;
    }

    .main > div {
        padding-top: 1rem;
    }

    /* Memory status indicator */
    .memory-status {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
        margin: 0.3rem;
        border: 2px solid;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-family: 'Orbitron', monospace;
    }

    .memory-on {
        background: linear-gradient(45deg, rgba(0, 255, 127, 0.2), rgba(0, 255, 255, 0.1));
        color: #00ff7f;
        border-color: #00ff7f;
        box-shadow: 0 0 20px rgba(0, 255, 127, 0.4), inset 0 0 20px rgba(0, 255, 127, 0.1);
        animation: pulse-green 2s infinite;
    }

    .memory-off {
        background: rgba(255, 100, 100, 0.15);
        color: #ff6464;
        border-color: #ff6464;
        box-shadow: 0 0 15px rgba(255, 100, 100, 0.3);
        animation: pulse-red 2s infinite;
    }

    @keyframes pulse-green {
        0%, 100% { box-shadow: 0 0 20px rgba(0, 255, 127, 0.4), inset 0 0 20px rgba(0, 255, 127, 0.1); }
        50% { box-shadow: 0 0 30px rgba(0, 255, 127, 0.8), inset 0 0 30px rgba(0, 255, 127, 0.2); }
    }

    @keyframes pulse-red {
        0%, 100% { box-shadow: 0 0 15px rgba(255, 100, 100, 0.3); }
        50% { box-shadow: 0 0 25px rgba(255, 100, 100, 0.6); }
    }

    /* Chat message styling */
    .chat-message {
        background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
        border: 1px solid rgba(0,255,255,0.2);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
        position: relative;
        overflow: hidden;
    }

    .chat-message::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, transparent, rgba(0,255,255,0.1), transparent);
        opacity: 0;
        transition: opacity 0.3s ease;
    }

    .chat-message:hover::before {
        opacity: 1;
    }

    .chat-message.question {
        border-left: 5px solid #00ffff;
        background: linear-gradient(135deg, rgba(0,255,255,0.1), rgba(0,255,255,0.05));
    }

    .chat-message.answer {
        border-left: 5px solid #ff00ff;
        background: linear-gradient(135deg, rgba(255,0,255,0.1), rgba(255,0,255,0.05));
    }

    .chat-message-with-context {
        border-left: 5px solid #00ff7f !important;
        box-shadow: 0 0 25px rgba(0, 255, 127, 0.3) !important;
        background: linear-gradient(135deg, rgba(0,255,127,0.15), rgba(0,255,127,0.05)) !important;
    }

    .chat-message-no-context {
        border-left: 5px solid #ff6464 !important;
        box-shadow: 0 0 25px rgba(255, 100, 100, 0.3) !important;
        background: linear-gradient(135deg, rgba(255,100,100,0.15), rgba(255,100,100,0.05)) !important;
    }

    /* Enhanced text styling */
    .chat-message strong {
        color: #00ffff;
        text-shadow: 0 0 10px rgba(0,255,255,0.5);
        font-family: 'Orbitron', monospace;
        font-size: 1.1rem;
        display: block;
        margin-bottom: 0.5rem;
    }

    .chat-message small {
        color: #ff00ff;
        font-family: 'Rajdhani', sans-serif;
        font-size: 0.9rem;
        opacity: 0.8;
    }

    /* Button enhancements */
    .stButton > button {
        background: linear-gradient(45deg, #00ffff, #ff00ff);
        border: none;
        border-radius: 25px;
        padding: 0.75rem 1.5rem;
        font-family: 'Orbitron', monospace;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 0 20px rgba(0,255,255,0.3);
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        box-shadow: 0 0 30px rgba(0,255,255,0.6);
        transform: translateY(-2px);
    }

    /* Input field styling */
    .stTextInput > div > div > input {
        background: rgba(0,0,0,0.7);
        border: 2px solid rgba(0,255,255,0.3);
        border-radius: 15px;
        color: #00ffff;
        padding: 1rem;
        font-family: 'Rajdhani', sans-serif;
        font-size: 1.1rem;
    }

    .stTextInput > div > div > input:focus {
        border-color: #00ffff;
        box-shadow: 0 0 20px rgba(0,255,255,0.5);
    }

    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, rgba(0,0,0,0.9), rgba(26,26,46,0.9));
        border-right: 2px solid rgba(0,255,255,0.2);
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        background: rgba(0,255,255,0.1);
        border-radius: 15px;
        border: 1px solid rgba(0,255,255,0.3);
        padding: 0.5rem 1rem;
        font-family: 'Orbitron', monospace;
        font-weight: 600;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(45deg, rgba(0,255,255,0.3), rgba(255,0,255,0.3));
        border-color: #00ffff;
        box-shadow: 0 0 15px rgba(0,255,255,0.4);
    }

    /* Expander styling */
    .streamlit-expander {
        background: rgba(0,0,0,0.5);
        border: 1px solid rgba(0,255,255,0.2);
        border-radius: 10px;
        backdrop-filter: blur(5px);
    }

    /* Info box styling */
    .stInfo {
        background: linear-gradient(45deg, rgba(0,255,255,0.1), rgba(0,255,127,0.1));
        border-left: 5px solid #00ff7f;
        border-radius: 10px;
    }

    .stWarning {
        background: linear-gradient(45deg, rgba(255,165,0,0.1), rgba(255,100,100,0.1));
        border-left: 5px solid #ff6464;
        border-radius: 10px;
    }

    .stSuccess {
        background: linear-gradient(45deg, rgba(0,255,127,0.1), rgba(0,255,255,0.1));
        border-left: 5px solid #00ff7f;
        border-radius: 10px;
    }

    .stError {
        background: linear-gradient(45deg, rgba(255,100,100,0.1), rgba(255,0,100,0.1));
        border-left: 5px solid #ff6464;
        border-radius: 10px;
    }

    /* Select box styling */
    .stSelectbox > div > div {
        background: rgba(0,0,0,0.7);
        border: 2px solid rgba(0,255,255,0.3);
        border-radius: 15px;
    }

    /* Slider styling */
    .stSlider > div > div > div > div {
        background: linear-gradient(90deg, #00ffff, #ff00ff);
    }

    /* Spinner styling */
    .stSpinner > div {
        border-top-color: #00ffff !important;
        border-right-color: #ff00ff !important;
    }

    /* Custom animations */
    @keyframes glow {
        0%, 100% { text-shadow: 0 0 20px rgba(0,255,255,0.5); }
        50% { text-shadow: 0 0 30px rgba(0,255,255,0.8), 0 0 40px rgba(255,0,255,0.5); }
    }

    .glow-text {
        animation: glow 2s ease-in-out infinite alternate;
    }

    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 12px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(0,0,0,0.3);
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb {
        background: linear-gradient(45deg, #00ffff, #ff00ff);
        border-radius: 10px;
        border: 2px solid rgba(0,0,0,0.3);
    }

    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(45deg, #ff00ff, #00ffff);
    }
</style>
""", unsafe_allow_html=True)

# Enhanced Title with animations
st.markdown("""
<div style="text-align: center; margin-bottom: 3rem;">
    <h1 class="glow-text" style="font-family: 'Orbitron', monospace; font-size: 4rem; background: linear-gradient(45deg, #00ffff, #ff00ff, #00ff7f); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 1rem;">🤖 AI Q&A</h1>
    <p style="color: #00ffff; font-size: 1.4rem; font-family: 'Rajdhani', sans-serif; text-shadow: 0 0 15px rgba(0,255,255,0.5);">
        ⚡ Enhanced Chatbot with Memory ⚡
    </p>
    <div style="width: 100px; height: 2px; background: linear-gradient(90deg, #00ffff, #ff00ff); margin: 1rem auto; border-radius: 1px;"></div>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "show_history" not in st.session_state:
    st.session_state.show_history = False
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "use_memory" not in st.session_state:
    st.session_state.use_memory = True
if "history_count" not in st.session_state:
    st.session_state.history_count = 0

# Enhanced Login/Register Section
if st.session_state.access_token is None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(0,255,255,0.1), rgba(255,0,255,0.1)); 
                    border: 2px solid rgba(0,255,255,0.3); border-radius: 20px; padding: 2rem; 
                    backdrop-filter: blur(10px); margin-bottom: 2rem;">
            <h3 style="text-align: center; color: #00ffff; font-family: 'Orbitron', monospace; 
                       text-shadow: 0 0 15px rgba(0,255,255,0.5); margin-bottom: 1rem;">🔐 USER LOGIN</h3>
        </div>
        """, unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["🔑 LOGIN", "📝 REGISTER"])

        with tab1:
            st.markdown("### 🚀 Sign Into Your Account")
            login_username = st.text_input("Username", key="login_user", placeholder="Enter your username")
            login_password = st.text_input("Password", type="password", key="login_pass",
                                           placeholder="Enter your password")

            if st.button("🚀 LOGIN", type="primary"):
                if login_username and login_password:
                    with st.spinner("🔥 Logging in..."):
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
                            st.success("✅ Login successful!")
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Invalid response from server")
                    else:
                        response_data = safe_json_response(res)
                        st.error(f"❌ {response_data.get('detail', 'Login failed.')}")
                else:
                    st.warning("⚠️ Please fill in both username and password")

        with tab2:
            st.markdown("### 🌟 Create New Account")
            reg_username = st.text_input("Username", key="reg_user", placeholder="Choose a username")
            reg_password = st.text_input("Password", type="password", key="reg_pass",
                                         placeholder="Create a strong password")

            if st.button("🔥 REGISTER", type="secondary"):
                if reg_username and reg_password:
                    if len(reg_password) < 6:
                        st.warning("⚠️ Password should be at least 6 characters long")
                    else:
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
                            st.success(f"✅ {response_data.get('message', 'Registration successful')}")
                            st.info("🔥 Switch to LOGIN tab to sign in")
                        else:
                            response_data = safe_json_response(res)
                            st.error(f"❌ {response_data.get('detail', 'Registration failed.')}")
                else:
                    st.warning("⚠️ Please fill in both username and password")

    # Add some animated footer for login page
    st.markdown("""
    <div style="text-align: center; margin-top: 3rem; padding: 2rem;">
        <div style="color: #00ffff; font-family: 'Orbitron', monospace; font-size: 1.2rem; 
                    text-shadow: 0 0 15px rgba(0,255,255,0.5);">
            ⚡ WELCOME TO THE FUTURE OF AI CHAT ⚡
        </div>
        <div style="margin-top: 1rem; color: #ff00ff; font-size: 0.9rem; opacity: 0.8;">
            Experience intelligent conversations with memory
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# Get chat history count
def update_history_count():
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    res, error = make_api_request("GET", f"{API_URL}/history/count", headers=headers)
    if not error and res and res.status_code == 200:
        response_data = safe_json_response(res)
        st.session_state.history_count = response_data.get("count", 0)


# Update history count
update_history_count()

# Enhanced Sidebar for logged-in users
with st.sidebar:
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(0,255,255,0.1), rgba(255,0,255,0.1)); 
                border-radius: 15px; padding: 1rem; margin-bottom: 1rem; text-align: center;">
        <h3 style="color: #00ffff; font-family: 'Orbitron', monospace; margin: 0;">🧠 USER PANEL</h3>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background: rgba(0,255,127,0.1); border: 1px solid rgba(0,255,127,0.3); 
                border-radius: 10px; padding: 1rem; margin-bottom: 1rem; text-align: center;">
        <strong style="color: #00ff7f; font-family: 'Orbitron', monospace;">{st.session_state.username}</strong>
        <br>
        <small style="color: #00ffff;">💬 {st.session_state.history_count} messages</small>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Memory/History Toggle Section
    st.markdown("### 🧠 CHAT MEMORY")

    memory_toggle = st.toggle(
        "Enable Chat Memory",
        value=st.session_state.use_memory,
        help="When enabled, the AI remembers previous conversations in this session"
    )
    st.session_state.use_memory = memory_toggle

    if st.session_state.use_memory:
        st.markdown('<span class="memory-status memory-on">🧠 MEMORY: ACTIVE</span>', unsafe_allow_html=True)

        # Memory settings
        max_history = st.slider(
            "Memory Length",
            min_value=3,
            max_value=20,
            value=10,
            help="Number of previous exchanges to remember"
        )

        st.markdown(f"""
        <div style="background: rgba(0,255,127,0.1); border-radius: 8px; padding: 0.5rem; margin: 0.5rem 0;">
            <small style="color: #00ff7f;">📚 Remembering last <strong>{max_history}</strong> exchanges</small>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.markdown('<span class="memory-status memory-off">🔥 MEMORY: DISABLED</span>', unsafe_allow_html=True)
        max_history = 0
        st.markdown("""
        <div style="background: rgba(255,100,100,0.1); border-radius: 8px; padding: 0.5rem; margin: 0.5rem 0;">
            <small style="color: #ff6464;">💭 Each message is independent</small>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Enhanced Model Selection
    st.markdown("### ⚡ AI MODEL")
    engine = st.selectbox(
        "Choose your AI model:",
        [
            "🚀 gemini-2.5-flash-lite-preview-06-17",
            "🧠 llama3-8b-8192",
            "💎 gemma2-9b-it",
            "⚡ llama-3.1-8b-instant",
        ],
        help="Each AI model has unique capabilities and response patterns"
    )

    # Display model info
    model_info = {
        "🚀 gemini-2.5-flash-lite-preview-06-17": "Google's latest Gemini - Fast & Intelligent",
        "🧠 llama3-8b-8192": "Meta's LLaMA 3 - Balanced & Reliable",
        "💎 gemma2-9b-it": "Google's Gemma 2 - Efficient & Smart",
        "⚡ llama-3.1-8b-instant": "Meta's LLaMA 3.1 - Lightning Fast"
    }

    st.markdown(f"""
    <div style="background: rgba(255,0,255,0.1); border-radius: 8px; padding: 0.5rem; margin: 0.5rem 0;">
        <small style="color: #ff00ff;">{model_info.get(engine, "Advanced AI Model")}</small>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Enhanced Action Buttons
    st.markdown("### 🛠️ ACTIONS")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📚 HISTORY", help="View complete chat history"):
            st.session_state.show_history = not st.session_state.show_history

    with col2:
        if st.button("🗑️ CLEAR", help="Clear all chat history"):
            headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
            res, error = make_api_request("DELETE", f"{API_URL}/history", headers=headers)

            if error:
                st.error(error)
            elif res and res.status_code == 200:
                response_data = safe_json_response(res)
                st.success(f"✅ {response_data.get('message', 'History cleared!')}")
                st.session_state.chat_messages = []
                update_history_count()
                st.rerun()
            else:
                st.error(f"❌ Clear failed")

    if st.button("🚪 LOGOUT", type="secondary", use_container_width=True, help="Logout from your account"):
        st.session_state.access_token = None
        st.session_state.username = None
        st.session_state.chat_messages = []
        st.session_state.show_history = False
        st.success("👋 Logged out successfully!")
        time.sleep(1)
        st.rerun()

    # Add sidebar footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 1rem;">
        <div style="color: #00ffff; font-size: 0.8rem; font-family: 'Orbitron', monospace;">
            ⚡ AI CHATBOT ACTIVE ⚡
        </div>
        <div style="color: #ff00ff; font-size: 0.7rem; margin-top: 0.5rem;">
            Enhanced with Memory
        </div>
    </div>
    """, unsafe_allow_html=True)

# Main Chat Interface
st.markdown("### 🚀 CHAT INTERFACE")

# Enhanced memory status display
if st.session_state.use_memory:
    st.info(f"🧠 **Memory Active**: AI remembers your last {max_history if 'max_history' in locals() else 10} exchanges")
else:
    st.warning("🔥 **Memory Disabled**: Each message is independent")

# Enhanced Chat Input
user_input = st.text_input(
    "💭 Send your question to the AI:",
    placeholder="Ask anything... The AI is listening! 🎯",
    key="chat_input_main"
)

col1, col2 = st.columns([8, 2])
with col2:
    send_button = st.button("🚀 SEND", type="primary")

# Process user input with enhanced feedback
if user_input and send_button:
    engine_name = engine.split(' ', 1)[1] if ' ' in engine else engine

    # Show processing status
    status_text = f"🧠 Processing with {engine_name}"
    if st.session_state.use_memory:
        status_text += " (with memory)"
    else:
        status_text += " (no memory)"

    with st.spinner(status_text):
        payload = {
            "question": user_input,
            "engine": engine_name,
            "use_history": st.session_state.use_memory,
            "max_history": max_history if st.session_state.use_memory else 0
        }
        headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
        res, error = make_api_request("POST", f"{API_URL}/ask", json=payload, headers=headers)

    if error:
        st.error(error)
    elif res and res.status_code == 200:
        response_data = safe_json_response(res)
        if "answer" in response_data:
            answer = response_data['answer']
            used_history = response_data.get('used_history', False)
            timestamp = datetime.now().strftime("%H:%M:%S")

            # Add to session messages
            st.session_state.chat_messages.append({
                "question": user_input,
                "answer": answer,
                "timestamp": timestamp,
                "engine": engine,
                "used_history": used_history
            })

            # Update history count and show success
            update_history_count()
            st.success("✅ Response generated successfully!")
            time.sleep(0.5)
            st.rerun()
        else:
            st.error("❌ Invalid response format from server")
    else:
        response_data = safe_json_response(res)
        st.error(f"❌ Request failed: {response_data.get('detail', 'Unknown error')}")

# Display recent chat messages with enhanced styling
if st.session_state.chat_messages:
    st.markdown("### 🧠 RECENT CONVERSATIONS")

    # Show last 3 messages
    for i, msg in enumerate(reversed(st.session_state.chat_messages[-3:])):
        memory_indicator = "chat-message-with-context" if msg.get('used_history') else "chat-message-no-context"
        memory_text = "🧠 WITH MEMORY" if msg.get('used_history') else "🔥 NO MEMORY"
        memory_icon = "🧠" if msg.get('used_history') else "💭"

        # Question
        st.markdown(f"""
        <div class="chat-message question {memory_indicator}">
            <strong>🤖 YOUR QUESTION:</strong> {msg['question']}
            <br><small>⚡ {msg['timestamp']} | 🔮 {msg['engine'].split(' ', 1)[1] if ' ' in msg['engine'] else msg['engine']} | {memory_icon} {memory_text}</small>
        </div>
        """, unsafe_allow_html=True)

        # Answer
        st.markdown(f"""
        <div class="chat-message answer {memory_indicator}">
            <strong>🧠 AI RESPONSE:</strong> {msg['answer']}
        </div>
        """, unsafe_allow_html=True)

        if i < len(st.session_state.chat_messages[-3:]) - 1:
            st.markdown('<div style="border-top: 1px solid rgba(255,255,255,0.1); margin: 1rem 0;"></div>',
                        unsafe_allow_html=True)

else:
    # Show welcome message when no chats
    st.markdown("""
    <div style="text-align: center; padding: 3rem; background: linear-gradient(135deg, rgba(0,255,255,0.05), rgba(255,0,255,0.05)); 
                border-radius: 20px; border: 1px solid rgba(0,255,255,0.2); margin: 2rem 0;">
        <h3 style="color: #00ffff; font-family: 'Orbitron', monospace; margin-bottom: 1rem;">🌟 Welcome to AI Chat!</h3>
        <p style="color: #ff00ff; font-size: 1.1rem;">Start a conversation by typing your question above</p>
        <div style="margin-top: 1rem;">
            <span style="color: #00ff7f;">💡 Tip: Enable memory for contextual conversations</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Show full chat history if toggled
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
            # Show history count
            st.markdown(f"""
            <div style="background: rgba(0,255,255,0.1); border-radius: 10px; padding: 1rem; margin-bottom: 1rem; text-align: center;">
                <strong style="color: #00ffff;">📊 Total Conversations: {len(history)}</strong>
            </div>
            """, unsafe_allow_html=True)

            # Display history in expandable format
            for i, chat in enumerate(history):
                created_time = chat.get('created_at', 'Unknown')[:19].replace('T', ' ')

                with st.expander(f"💬 Chat {len(history) - i} - {created_time}", expanded=False):
                    st.markdown(f"""
                    <div style="background: rgba(0,255,255,0.05); border-radius: 10px; padding: 1rem; margin: 0.5rem 0;">
                        <strong style="color: #00ffff;">🤖 YOUR QUESTION:</strong><br>
                        <span style="color: #ffffff;">{chat.get('question', 'N/A')}</span>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown(f"""
                    <div style="background: rgba(255,0,255,0.05); border-radius: 10px; padding: 1rem; margin: 0.5rem 0;">
                        <strong style="color: #ff00ff;">🧠 AI RESPONSE:</strong><br>
                        <span style="color: #ffffff;">{chat.get('answer', 'N/A')}</span>
                    </div>
                    """, unsafe_allow_html=True)

                    if 'created_at' in chat:
                        st.caption(f"⚡ Time: {created_time}")
        else:
            st.markdown("""
            <div style="text-align: center; padding: 2rem; background: rgba(255,165,0,0.1); 
                        border-radius: 15px; border: 1px solid rgba(255,165,0,0.3);">
                <h4 style="color: #ffa500;">🌌 No chat history found</h4>
                <p style="color: #ffffff;">Start asking questions to build your conversation history!</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        response_data = safe_json_response(res)
        st.error(f"❌ Unable to load history: {response_data.get('detail', 'Unknown error')}")

# Enhanced footer with stats
st.markdown('<div style="border-top: 2px solid rgba(0,255,255,0.3); margin: 3rem 0 1rem 0;"></div>',
            unsafe_allow_html=True)

# Real-time stats
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("💬 Messages", st.session_state.history_count)
with col2:
    st.metric("🧠 Memory", "ON" if st.session_state.use_memory else "OFF")
with col3:
    current_engine = engine.split(' ', 1)[1] if ' ' in engine else engine
    st.metric("🔮 Model", current_engine.split('-')[0].upper())
with col4:
    st.metric("👤 User", st.session_state.username)

# Animated footer
st.markdown(f"""
<div style="text-align: center; color: #00ffff; padding: 2rem; font-family: 'Orbitron', monospace;">
    <div style="font-size: 1.4rem; margin-bottom: 0.5rem; text-shadow: 0 0 20px rgba(0,255,255,0.6);" class="glow-text">
        ⚡ AI CHATBOT SYSTEM ACTIVE ⚡
    </div>
    <div style="font-size: 1rem; opacity: 0.9; color: #ff00ff; margin-bottom: 1rem;">
        🧠 Memory: {'ACTIVE' if st.session_state.use_memory else 'DISABLED'} • 💬 Total Messages: {st.session_state.history_count} • 👤 User: {st.session_state.username}
    </div>
    <div style="margin-top: 1.5rem; font-size: 0.8rem; color: #00ff7f; opacity: 0.7;">
        [ ENHANCED CHATBOT WITH CONVERSATION MEMORY & MULTIPLE AI MODELS ]
    </div>
    <div style="margin-top: 1rem;">
        <div style="width: 200px; height: 2px; background: linear-gradient(90deg, #00ffff, #ff00ff, #00ff7f); 
                    margin: 0 auto; border-radius: 1px; animation: glow 2s infinite;"></div>
    </div>
</div>
""", unsafe_allow_html=True)

# Add some JavaScript for enhanced interactivity (optional)
st.markdown("""
<script>
// Auto-scroll to bottom when new messages arrive
function scrollToBottom() {
    window.scrollTo({
        top: document.body.scrollHeight,
        behavior: 'smooth'
    });
}

// Add some interactive effects
document.addEventListener('DOMContentLoaded', function() {
    // Add hover effects to chat messages
    const chatMessages = document.querySelectorAll('.chat-message');
    chatMessages.forEach(message => {
        message.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.transition = 'all 0.3s ease';
        });
        message.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0px)';
        });
    });
});
</script>
""", unsafe_allow_html=True)