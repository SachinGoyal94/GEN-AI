import streamlit as st
import requests
import time

# -----------------------------------------------------
# 🌐 Backend Configuration
# -----------------------------------------------------
# Change this if deployed elsewhere (e.g., Render, Vercel)
BACKEND_URL = "http://127.0.0.1:8000/chat"

# -----------------------------------------------------
# 🎨 Streamlit Page Config
# -----------------------------------------------------
st.set_page_config(
    page_title="Database Speaks - SQL Chatbot",
    page_icon="🗣️",
    layout="wide",
)

# -----------------------------------------------------
# 💅 Custom CSS Styling
# -----------------------------------------------------
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    .chat-box {
        max-height: 500px;
        overflow-y: auto;
        margin-top: 1rem;
        padding: 1rem;
        border-radius: 12px;
        background: #f9f9fb;
        border: 1px solid #e0e0e0;
    }
    .user {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;  /* user text white */
        padding: 0.75rem 1rem;
        border-radius: 15px 15px 0 15px;
        margin-bottom: 0.5rem;
        text-align: right;
    }
    .bot {
        background: #f1f3f4;
        color: black !important;  /* bot text black */
        padding: 0.75rem 1rem;
        border-radius: 15px 15px 15px 0;
        margin-bottom: 0.5rem;
    }
    .success-box {
        background: #e6ffee;
        color: #1a7f37;
        padding: 0.75rem;
        border-left: 5px solid #28a745;
        border-radius: 6px;
    }
    .error-box {
        background: #ffe6e6;
        color: #c0392b;
        padding: 0.75rem;
        border-left: 5px solid #e74c3c;
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------
# 🏷️ Header
# -----------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>🗣️ Database Speaks</h1>
    <p>Talk to your database — now powered by FastAPI + Groq</p>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------
# 🧠 Sidebar Configuration
# -----------------------------------------------------
st.sidebar.header("⚙️ Database Configuration")

db_type = st.sidebar.radio("Select Database Type", ["SQLite", "MySQL"])

mysql_host = mysql_user = mysql_password = mysql_db = mysql_port = None

if db_type == "MySQL":
    mysql_host = st.sidebar.text_input("Host", "localhost")
    mysql_user = st.sidebar.text_input("Username", "root")
    mysql_password = st.sidebar.text_input("Password", type="password")
    mysql_db = st.sidebar.text_input("Database Name", "mydb")
    mysql_port = st.sidebar.text_input("Port", "3306")
    st.sidebar.markdown("---")
    if st.sidebar.button("🔍 Test Connection"):
        if all([mysql_host, mysql_user, mysql_password, mysql_db]):
            import mysql.connector

            try:
                port = int(mysql_port) if mysql_port else 3306
                conn = mysql.connector.connect(
                    host=mysql_host,
                    user=mysql_user,
                    password=mysql_password,
                    database=mysql_db,
                    port=port
                )
                conn.close()
                st.sidebar.success("✅ Connection successful!")
            except Exception as e:
                st.sidebar.error(f"❌ Connection failed: {str(e)}")
        else:
            st.sidebar.warning("⚠️ Please fill in all MySQL connection details")

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Clear Chat History"):
    st.session_state["chat_history"] = []
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

# -----------------------------------------------------
# 💬 Chat History Initialization
# -----------------------------------------------------
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = [
        {"role": "assistant", "content": "Hello 👋! I'm your SQL AI assistant. Ask me anything about your database."}
    ]

# -----------------------------------------------------
# 💭 Chat Interface
# -----------------------------------------------------
st.markdown("### 💬 Chat with your database")

# Chat history display
chat_box = st.container()
with chat_box:
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"<div class='user'>👤 You: {msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='bot'>🤖 {msg['content']}</div>", unsafe_allow_html=True)

# -----------------------------------------------------
# ✏️ User Input
# -----------------------------------------------------
user_query = st.chat_input("Ask your database... (e.g., Show top 5 students)")

if user_query:
    # Add user query to session
    st.session_state.chat_history.append({"role": "user", "content": user_query})

    # Display loading spinner
    with st.spinner("🗣️ Thinking... asking your database..."):
        payload = {
            "query": user_query,
            "db_type": db_type.lower(),
            "mysql_host": mysql_host,
            "mysql_user": mysql_user,
            "mysql_password": mysql_password,
            "mysql_db": mysql_db,
            "mysql_port": mysql_port
        }

        try:
            res = requests.post(BACKEND_URL, json=payload, timeout=60)

            if res.status_code == 200:
                data = res.json()
                ai_response = data.get("response", "No response from AI.")
                st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
                st.markdown(f"<div class='bot'>🤖 {ai_response}</div>", unsafe_allow_html=True)
            else:
                st.error(f"Error {res.status_code}: {res.text}")
                st.session_state.chat_history.append({"role": "assistant", "content": f"❌ Error: {res.text}"})

        except requests.exceptions.RequestException as e:
            st.error(f"⚠️ Request failed: {e}")
            st.session_state.chat_history.append(
                {"role": "assistant", "content": f"⚠️ Unable to reach backend: {str(e)}"}
            )

# -----------------------------------------------------
# 📘 Footer
# -----------------------------------------------------
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#666;'>🗣️ <b>Database Speaks</b> — Powered by FastAPI + LangChain + Groq</div>",
    unsafe_allow_html=True,
)
