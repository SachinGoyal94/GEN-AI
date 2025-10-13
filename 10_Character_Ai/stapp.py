import streamlit as st
import requests

# ----------------- CONFIG -----------------
BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Character Chat", layout="centered")

st.title("🗣️ Character Chat (Gemini Backend)")

# ----------------- CHARACTER SETUP -----------------
st.header("1️⃣ Initialize Character")

mode = st.radio("Choose character mode:", ["Auto (Known)", "Custom (Your own)"], index=0)

if mode == "Auto (Known)":
    auto_name = st.text_input("Enter character name:", value="Gandhi")
    tone = st.selectbox("Tone / style:", ["neutral", "serious", "funny", "romantic", "mature"], index=0)

    if st.button("Initialize Auto Character"):
        response = requests.post(
            f"{BACKEND_URL}/set_character/",
            data={
                "mode": "auto",
                "character_name": auto_name,
                "tone": tone
            }
        )
        if response.ok:
            st.success("✅ Character initialized successfully!")
            st.json(response.json())
        else:
            st.error(response.json().get("error", "Error initializing character"))

else:
    custom_prompt = st.text_area("Describe your custom character:")
    tone = st.selectbox("Tone / style:", ["neutral", "serious", "funny", "romantic", "mature"], index=0)

    if st.button("Initialize Custom Character"):
        response = requests.post(
            f"{BACKEND_URL}/set_character/",
            data={
                "mode": "custom",
                "custom_prompt": custom_prompt,
                "tone": tone
            }
        )
        if response.ok:
            st.success("🎨 Custom character created!")
            st.json(response.json())
        else:
            st.error(response.json().get("error", "Error creating character"))

# ----------------- CHAT -----------------
st.header("2️⃣ Chat with Character")

user_message = st.text_input("Type your message:")

if st.button("Send Message") and user_message:
    response = requests.post(
        f"{BACKEND_URL}/chat/",
        data={"user_message": user_message}
    )
    if response.ok:
        chat_response = response.json().get("response", "")
        st.markdown(f"**Character:** {chat_response}")
    else:
        st.error(response.json().get("error", "Error sending message"))
