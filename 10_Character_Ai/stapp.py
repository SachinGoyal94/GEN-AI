import streamlit as st
import requests

# ================== CONFIG ==================
st.set_page_config(page_title="Character Chat", page_icon="🎭", layout="centered")

BACKEND_URL = "http://127.0.0.1:8000"  # FastAPI backend

# ================== STYLING ==================
st.markdown("""
    <style>
    .title { text-align: center; font-size: 36px; font-weight: 700; color: #FF4B4B; margin-bottom: 0.2em; }
    .subtitle { text-align: center; color: #888; margin-bottom: 2em; }
    .chat-bubble-user { background-color: #DCF8C6; padding: 0.8em 1em; border-radius: 1em; margin: 0.4em 0; max-width: 80%; align-self: flex-end; }
    .chat-bubble-character { background-color: #E8E8E8; padding: 0.8em 1em; border-radius: 1em; margin: 0.4em 0; max-width: 80%; align-self: flex-start; }
    </style>
""", unsafe_allow_html=True)

# ================== HEADER ==================
st.markdown("<div class='title'>🎬 Character Chat</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Talk to your favorite fictional characters — powered by AI</div>", unsafe_allow_html=True)

# ================== SESSION STATE ==================
if "character_name" not in st.session_state:
    st.session_state.character_name = None
if "summary" not in st.session_state:
    st.session_state.summary = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ================== CHARACTER INITIALIZATION ==================
st.header("✨ Choose a Character")

character_input = st.text_input("Enter a character name (e.g., Iron Man, Sherlock Holmes, Hermione Granger):")

if st.button("Generate Character Summary"):
    if not character_input.strip():
        st.warning("Please enter a character name.")
    else:
        with st.spinner(f"Generating {character_input}'s profile..."):
            try:
                response = requests.post(f"{BACKEND_URL}/set_character/", data={"character_name": character_input})
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.character_name = character_input
                    st.session_state.summary = data["summary"]
                    st.session_state.chat_history = []
                    st.success(f"✅ {character_input} is ready to chat!")
                else:
                    st.error(f"Failed to generate character: {response.text}")
            except Exception as e:
                st.error(f"Connection error: {e}")

if st.session_state.summary:
    with st.expander(f"📜 {st.session_state.character_name}'s Summary", expanded=False):
        st.markdown(st.session_state.summary)

# ================== CHAT INTERFACE ==================
if st.session_state.character_name:
    st.header(f"💬 Chat with {st.session_state.character_name}")

    user_message = st.text_input("Your message:", key="user_message_input")

    if st.button("Send"):
        if not user_message.strip():
            st.warning("Please type a message first.")
        else:
            st.session_state.chat_history.append({"sender": "user", "text": user_message})

            with st.spinner(f"{st.session_state.character_name} is thinking..."):
                try:
                    response = requests.post(f"{BACKEND_URL}/chat/", data={"user_message": user_message})
                    if response.status_code == 200:
                        data = response.json()
                        reply = data.get("response", "No response.")
                        st.session_state.chat_history.append({"sender": "character", "text": reply})
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")

    # Display chat history
    st.markdown("### 🗨️ Conversation")
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            if msg["sender"] == "user":
                st.markdown(f"<div class='chat-bubble-user'><b>You:</b> {msg['text']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='chat-bubble-character'><b>{st.session_state.character_name}:</b> {msg['text']}</div>", unsafe_allow_html=True)
