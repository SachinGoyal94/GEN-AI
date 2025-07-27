import os
from dotenv import load_dotenv

load_dotenv()
import streamlit as st
from langchain.agents import create_sql_agent
from pathlib import Path
from langchain.sql_database import SQLDatabase
from langchain.agents.agent_types import AgentType
from langchain.callbacks import StreamlitCallbackHandler
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from sqlalchemy import create_engine
import sqlite3
from langchain_groq import ChatGroq
import time

# Page configuration with custom styling
st.set_page_config(
    page_title="Database Speaks - AI SQL Assistant",
    page_icon="🗣️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful styling
st.markdown("""
<style>
    /* Main container styling */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }

    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }

    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }

    /* Sidebar styling */
    .sidebar-content {
        background: #f8f9ff;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
    }

    /* Chat message styling */
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 15px 15px 5px 15px;
        margin: 0.5rem 0;
        max-width: 80%;
        margin-left: auto;
        box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
    }

    .assistant-message {
        background: #f1f3f4;
        color: #333;
        padding: 1rem;
        border-radius: 15px 15px 15px 5px;
        margin: 0.5rem 0;
        max-width: 80%;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }

    /* Status indicators */
    .status-success {
        background: #d4edda;
        color: #155724;
        padding: 0.75rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
    }

    .status-error {
        background: #f8d7da;
        color: #721c24;
        padding: 0.75rem;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
    }

    .status-info {
        background: #cce7ff;
        color: #004085;
        padding: 0.75rem;
        border-radius: 8px;
        border-left: 4px solid #007bff;
        margin: 1rem 0;
    }

    /* Connection card */
    .connection-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
        border: 1px solid #e0e0e0;
    }

    /* Feature highlights */
    .feature-box {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        text-align: center;
    }

    .stTextInput > div > div > input {
        border-radius: 20px;
        border: 2px solid #e0e0e0;
        padding: 0.5rem 1rem;
    }

    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown("""
<div class="main-header">
    <h1>🤖 SQL AI Assistant</h1>
    <p>Where your databases find their voice through AI-powered conversations</p>
</div>
""", unsafe_allow_html=True)

# Database configuration constants
LOCALDB = "USE_LOCALDB"
MYSQL = "USE_MYSQL"

# Sidebar for database configuration
with st.sidebar:
    st.markdown("### 🔧 Database Configuration")

    # Database selection with enhanced UI
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)

    radio_opt = [
        "🗃️ Use SQLite Database (students.db)",
        "🔗 Connect to MySQL Database"
    ]
    selected_opt = st.radio(
        "Choose your database:",
        options=radio_opt,
        help="Select the database you want to chat with"
    )

    st.markdown('</div>', unsafe_allow_html=True)

    # Database connection setup
    if radio_opt.index(selected_opt) == 1:
        db_uri = MYSQL
        st.markdown("#### MySQL Connection Details")

        with st.container():
            st.markdown('<div class="connection-card">', unsafe_allow_html=True)
            mysql_host = st.text_input("🌐 Host", placeholder="localhost",
                                       help="Server address (e.g., localhost, 127.0.0.1, or your server IP)")
            mysql_user = st.text_input("👤 Username", placeholder="root",
                                       help="Database username (commonly 'root' for local MySQL)")
            mysql_password = st.text_input("🔒 Password", type="password", help="Your MySQL password")
            mysql_db = st.text_input("🗄️ Database Name", placeholder="mydb",
                                     help="Name of the database you want to connect to")
            mysql_port = st.text_input("🔌 Port", placeholder="3306", help="MySQL port (default is 3306)")
            st.markdown('</div>', unsafe_allow_html=True)

            # Connection test button
            if st.button("🔍 Test Connection", type="secondary"):
                if all([mysql_host, mysql_user, mysql_password, mysql_db]):
                    try:
                        port = mysql_port if mysql_port else "3306"
                        test_engine = create_engine(
                            f"mysql+mysqlconnector://{mysql_user}:{mysql_password}@{mysql_host}:{port}/{mysql_db}")
                        test_connection = test_engine.connect()
                        test_connection.close()
                        st.success("✅ Connection successful!")
                    except Exception as e:
                        st.error(f"❌ Connection failed: {str(e)}")
                        st.info("💡 Common issues: Check host address, credentials, and ensure MySQL server is running")
                else:
                    st.warning("⚠️ Please fill in all connection details")

        # Enhanced troubleshooting guide
        st.markdown("""
        <div class="status-info">
            <strong>💡 Connection Guide:</strong><br>
            <strong>Host Examples:</strong><br>
            • localhost (local MySQL)<br>
            • 127.0.0.1 (local IP)<br>
            • your-server-ip.com<br><br>
            <strong>Password Encoding:</strong><br>
            • @ → %40 • : → %3A • / → %2F<br>
            • # → %23 • ? → %3F • & → %26<br><br>
            <strong>Common Issues:</strong><br>
            • Ensure MySQL server is running<br>
            • Check firewall settings<br>
            • Verify database exists<br>
            • Use correct port (default: 3306)
        </div>
        """, unsafe_allow_html=True)
    else:
        db_uri = LOCALDB
        st.markdown("""
        <div class="status-success">
            <strong>✅ SQLite Database Selected</strong><br>
            Using local students.db file
        </div>
        """, unsafe_allow_html=True)

    # Clear chat history button
    st.markdown("---")
    if st.button("🗑️ Clear Chat History", type="secondary", use_container_width=True):
        st.session_state["messages"] = [{"role": "assistant",
                                         "content": "Hello! Welcome to Database Speaks! 🗣️ I'm here to help your database find its voice. What would you like to know? 💬"}]
        st.experimental_rerun()

# API Key configuration
api_key = os.getenv("GROQ_KEY") or st.secrets.get("GROQ_KEY")

if not api_key:
    st.markdown("""
    <div class="status-error">
        <strong>⚠️ API Key Missing</strong><br>
        Please set your GROQ_KEY in environment variables or Streamlit secrets.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Initialize LLM
try:
    llm = ChatGroq(groq_api_key=api_key, model="gemma2-9b-it", streaming=True)
    st.markdown("""
    <div class="status-success">
        <strong>🤖 AI Model Loaded</strong> - Your database is ready to speak with Gemma2-9B
    </div>
    """, unsafe_allow_html=True)
except Exception as e:
    st.markdown(f"""
    <div class="status-error">
        <strong>❌ Model Loading Failed</strong><br>
        {str(e)}
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# Database configuration function
@st.cache_resource(ttl="2h")
def configure_db(db_uri, mysql_host=None, mysql_user=None, mysql_password=None, mysql_db=None, mysql_port=None):
    if db_uri == LOCALDB:
        dbfilepath = (Path(__file__).parent / "students.db").absolute()
        if not dbfilepath.exists():
            st.error("❌ students.db file not found!")
            return None
        creator = lambda: sqlite3.connect(f"file:{dbfilepath}?mode=ro", uri=True)
        return SQLDatabase(create_engine("sqlite:///", creator=creator))
    elif db_uri == MYSQL:
        if not all([mysql_host, mysql_user, mysql_password, mysql_db]):
            st.error("❌ Please provide all MySQL connection details.")
            return None
        try:
            port = mysql_port if mysql_port else "3306"
            connection_string = f"mysql+mysqlconnector://{mysql_user}:{mysql_password}@{mysql_host}:{port}/{mysql_db}"
            return SQLDatabase(create_engine(connection_string))
        except Exception as e:
            error_msg = str(e)
            if "Unknown MySQL server host" in error_msg:
                st.error(f"❌ Cannot connect to MySQL host '{mysql_host}'. Please check:")
                st.error("• Host address is correct (e.g., 'localhost', '127.0.0.1')")
                st.error("• MySQL server is running")
                st.error("• Network connectivity")
            elif "Access denied" in error_msg:
                st.error("❌ Access denied. Please check:")
                st.error("• Username and password are correct")
                st.error("• User has permissions for the database")
            elif "Unknown database" in error_msg:
                st.error(f"❌ Database '{mysql_db}' not found. Please check:")
                st.error("• Database name is spelled correctly")
                st.error("• Database exists on the server")
            else:
                st.error(f"❌ Database connection failed: {error_msg}")
            return None


# Configure database
if db_uri == MYSQL:
    db = configure_db(db_uri, mysql_host, mysql_user, mysql_password, mysql_db, mysql_port)
else:
    db = configure_db(db_uri)

if db is None:
    st.stop()

# Initialize agent
try:
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    agent = create_sql_agent(
        llm,
        toolkit,
        verbose=True,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION
    )

    # Display database info
    tables = db.get_usable_table_names()
    if tables:
        st.markdown(f"""
        <div class="status-success">
            <strong>🗣️ Database Connected & Speaking!</strong><br>
            Your database is ready to share insights from: {', '.join(tables)}
        </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.markdown(f"""
    <div class="status-error">
        <strong>❌ Agent Setup Failed</strong><br>
        {str(e)}
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant",
         "content": "Hello! Welcome to Database Speaks! 🗣️ I'm here to help your database find its voice. What would you like to know? 💬"}
    ]

# Display chat history with beautiful styling
st.markdown("### 💬 Database Conversation")
chat_container = st.container()

with chat_container:
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="user-message">
                <strong>You:</strong> {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="assistant-message">
                <strong>🗣️ Database Says:</strong> {message["content"]}
            </div>
            """, unsafe_allow_html=True)

# Chat input with enhanced styling
st.markdown("### 💭 What do you want to ask your database?")
user_query = st.chat_input(
    placeholder="Ask your database anything... (e.g., 'What stories do you hold?' or 'Show me your most interesting data')",
    key="chat_input"
)

# Handle user input
if user_query:
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_query})

    # Display user message immediately
    st.markdown(f"""
    <div class="user-message">
        <strong>You:</strong> {user_query}
    </div>
    """, unsafe_allow_html=True)

    # Process with agent
    with st.spinner("🗣️ Your database is speaking..."):
        try:
            # Create callback handler
            streamlit_callback_handler = StreamlitCallbackHandler(st.container())

            # Get response from agent
            response = agent.run(user_query, callbacks=[streamlit_callback_handler])

            # Add assistant response to history
            st.session_state.messages.append({"role": "assistant", "content": response})

            # Display response
            st.markdown(f"""
            <div class="assistant-message">
                <strong>🗣️ Database Says:</strong> {response}
            </div>
            """, unsafe_allow_html=True)

        except Exception as e:
            error_message = f"I encountered an error while processing your request: {str(e)}"
            st.session_state.messages.append({"role": "assistant", "content": error_message})

            st.markdown(f"""
            <div class="status-error">
                <strong>❌ Error:</strong> {error_message}
            </div>
            """, unsafe_allow_html=True)

# Footer with features
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-box">
        <strong>🗣️ Voice to Data</strong><br>
        Your database speaks naturally
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-box">
        <strong>📊 Multi-Platform</strong><br>
        SQLite & MySQL conversations
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-box">
        <strong>🤖 AI Intelligence</strong><br>
        Smart database interpreter
    </div>
    """, unsafe_allow_html=True)

# Sample queries section
with st.expander("💡 Start the Conversation - Sample Questions"):
    st.markdown("""
    **Getting to Know Your Database:**
    - "What can you tell me about yourself?"
    - "What stories do your tables hold?"
    - "How much data do you contain?"

    **Let Your Data Speak:**
    - "Show me your most interesting records"
    - "What patterns do you see in your data?"
    - "Tell me about your top performers"

    **Deep Database Conversations:**
    - "What would you like me to know about your structure?"
    - "Share some insights I might find surprising"
    - "What questions should I be asking you?"
    """)

# Add a subtle footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <small>🗣️ <strong>Database Speaks</strong> - Where every database has a voice and every query starts a conversation</small>
</div>
""", unsafe_allow_html=True)