import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.title("🔐 Secure Q&A Chatbot with JWT")

# ✅ Initialize session state keys
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "show_history" not in st.session_state:
    st.session_state.show_history = False

# ✅ If not logged in: show Register/Login
if st.session_state.access_token is None:
    st.subheader("Register or Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Register"):
        res = requests.post(f"{API_URL}/register", json={"username": username, "password": password})
        if res.status_code == 200:
            st.success(res.json()["message"])
        else:
            st.error(res.json().get("detail", "Registration failed."))

    if st.button("Login"):
        res = requests.post(
            f"{API_URL}/token",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if res.status_code == 200:
            st.session_state.access_token = res.json()["access_token"]
            st.session_state.username = username  # ✅ Save username
            st.success("✅ Login successful!")
            st.rerun()
        else:
            st.error(res.json().get("detail", "Login failed."))

    st.stop()

# ✅ If logged in
st.sidebar.write(f"👤 Logged in as: `{st.session_state.username}`")

if st.sidebar.button("🚪 Logout"):
    st.session_state.access_token = None
    st.session_state.username = None
    st.rerun()

# ✅ Toggle chat history
if st.sidebar.button("🗂️ Toggle Chat History"):
    st.session_state.show_history = not st.session_state.show_history

# ✅ Delete chat history
if st.sidebar.button("🗑️ Delete Chat History"):
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    res = requests.delete(f"{API_URL}/history", headers=headers)
    if res.status_code == 200:
        st.success("✅ Chat history cleared!")
    else:
        st.error("❌ Failed to clear chat history.")

# ✅ Ask a question
engine = st.sidebar.selectbox(
    "Select LLM model",
    [
        "gemini-2.5-flash-lite-preview-06-17",
        "llama3-8b-8192",
        "gemma2-9b-it",
        "llama-3.1-8b-instant",
        "llama3.2:latest",
        "gemma3:1b"
    ]
)

st.write("Ask your question below:")
user_input = st.text_input("You:")

if user_input:
    payload = {"question": user_input, "engine": engine}
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    res = requests.post(f"{API_URL}/ask", json=payload, headers=headers)
    if res.status_code == 200:
        st.write(f"**Answer:** {res.json()['answer']}")
    else:
        st.error("❌ Failed to get answer.")

# ✅ Show chat history if toggled
if st.session_state.show_history:
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    res = requests.get(f"{API_URL}/history", headers=headers)
    if res.status_code == 200:
        st.subheader("🗂️ Your Chat History")
        for chat in res.json():
            st.markdown(f"**Q:** {chat['question']}")
            st.markdown(f"**A:** {chat['answer']}")
            st.caption(f"Time: {chat['created_at']}")
            st.write("---")
    else:
        st.error("❌ Failed to load chat history.")