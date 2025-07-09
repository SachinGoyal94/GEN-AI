import streamlit as st
import requests

st.title("Enhanced Q&A Chatbot With Gemini")

# Sidebar settings
st.sidebar.title("Settings")
api_key = st.sidebar.text_input("Your Gemini API Key:", type="password")
engine = st.sidebar.selectbox("Gemini Model", ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.5-pro"])

# Prompt input
st.write("Go ahead and ask any question:")
user_input = st.text_input("You:")

user_id = "user_123"  # Use session ID or auth system in real app

if user_input and api_key:
    payload = {
        "user_id": user_id,
        "question": user_input,
        "engine": engine
    }

    response = requests.post("http://localhost:8000/ask", json=payload)
    answer = response.json()["answer"]
    st.write(answer)

elif user_input:
    st.warning("Please enter the Gemini API Key in the sidebar.")
