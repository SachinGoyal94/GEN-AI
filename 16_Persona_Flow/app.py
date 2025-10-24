# persona_frontend.py
import streamlit as st
import requests
from datetime import datetime

# ==================== CONFIG ====================
BACKEND_URL = "http://127.0.0.1:8000"  # Change if deployed online

st.set_page_config(page_title="Persona Flow Chat", page_icon="🧑‍🤝‍🧑", layout="wide")

# ==================== SESSION STATE ====================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # stores dicts: {"user":..., "ai":...}

if "character" not in st.session_state:
    st.session_state.character = None  # stores dict: {"name":..., "mode":..., "tone":...}


# ==================== FUNCTIONS ====================
def set_character(mode, character_name=None, custom_prompt=None, tone="neutral"):
    payload = {
        "mode": mode,
        "character_name": character_name,
        "custom_prompt": custom_prompt,
        "tone": tone
    }
    response = requests.post(f"{BACKEND_URL}/set_character/", data=payload)
    if response.status_code == 200:
        data = response.json()
        st.session_state.character = {
            "name": character_name if mode == "auto" else "Custom Character",
            "mode": mode,
            "tone": tone,
            "summary": data.get("summary")
        }
        st.success(f"✅ Character set successfully! ({tone} tone)")
    else:
        st.error(f"❌ Failed to set character: {response.text}")


def chat_with_character(message):
    payload = {"user_message": message}
    response = requests.post(f"{BACKEND_URL}/chat/", data=payload)
    if response.status_code == 200:
        data = response.json()
        reply = data.get("response", "No response from AI.")
        st.session_state.chat_history.append({"user": message, "ai": reply})
    else:
        st.error(f"❌ Failed to get AI response: {response.text}")


# ==================== UI ====================
st.title("🧑‍🤝‍🧑 Persona Flow Chat")
st.write("Chat with any character (auto or custom)")

# --- CHARACTER SETUP ---
st.sidebar.header("Step 1: Create / Select Character")
mode = st.sidebar.radio("Mode", ["auto", "custom"], index=0)

if mode == "auto":
    auto_name = st.sidebar.text_input("Character Name", value="Gandhi")
    tone = st.sidebar.selectbox("Tone", ["neutral", "serious", "funny", "romantic", "mature"], index=0)
    if st.sidebar.button("Initialize Auto Character"):
        set_character(mode="auto", character_name=auto_name, tone=tone)

elif mode == "custom":
    custom_prompt = st.sidebar.text_area("Describe your character concept",
                                         value="A funny AI assistant who loves jokes")
    tone = st.sidebar.selectbox("Tone", ["neutral", "serious", "funny", "romantic", "mature"], index=2)
    if st.sidebar.button("Create Custom Character"):
        set_character(mode="custom", custom_prompt=custom_prompt, tone=tone)

# --- CHAT INTERFACE ---
if st.session_state.character:
    st.subheader(f"Chatting as: {st.session_state.character['name']} ({st.session_state.character['tone']} tone)")

    message = st.text_input("Type your message here...", key="user_input")

    if st.button("Send") and message:
        chat_with_character(message)
        st.session_state.user_input = ""  # clear input box

    # Display chat history
    st.markdown("---")
    st.subheader("Conversation")
    for chat in st.session_state.chat_history:
        st.markdown(f"**You:** {chat['user']}")
        st.markdown(f"**{st.session_state.character['name']}:** {chat['ai']}")
        st.markdown("---")
else:
    st.info("Please select or create a character from the sidebar to start chatting.")
