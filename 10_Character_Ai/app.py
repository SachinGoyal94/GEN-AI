import streamlit as st
import os
from crew import build_character_crew
from character_info import get_character_summary
from llm import groq_llm


st.set_page_config(
    page_title="Character Chat 💬",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.title("🧙‍♂️ Character Chat from Any Book or Movie")
st.markdown("Upload a PDF of a book or script and chat with any character from it!")

if "character_summary" not in st.session_state:
    st.session_state.character_summary = ""
if "character_name" not in st.session_state:
    st.session_state.character_name = ""
if "pdf_processed" not in st.session_state:
    st.session_state.pdf_processed = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.sidebar:
    st.header("📚 Character Setup")

    # Character name input
    character_name = st.text_input(
        "Enter Character Name",
        value=st.session_state.character_name,
        help="Enter the name of the character you want to chat with"
    )

    uploaded_file = st.file_uploader(
        "Upload Character Document (PDF)",
        type=['pdf'],
        help="Upload a PDF containing information about the character"
    )

    if st.button("🔄 Process Character", type="primary"):
        if not uploaded_file or not character_name:
            st.error("Please provide both a character name and upload a PDF file.")
        else:
            with st.spinner("Processing character information..."):
                try:
                    # Create directory for character documents
                    os.makedirs("character_docs", exist_ok=True)

                    # Save uploaded file
                    file_path = f"character_docs/{character_name}_document.pdf"
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.read())

                    summary = get_character_summary(character_name, file_path)

                    st.session_state.character_summary = summary
                    st.session_state.character_name = character_name
                    st.session_state.pdf_processed = True
                    st.session_state.chat_history = []  # Clearing the previous chat history

                    st.success(f"✅ {character_name} is ready to chat!")

                except Exception as e:
                    st.error(f"Error processing character: {str(e)}")

    if st.session_state.pdf_processed:
        st.success(f"✅ {st.session_state.character_name} is loaded")

        with st.expander("📄 Character Summary"):
            st.text_area(
                "Character Information",
                value=st.session_state.character_summary,
                height=200,
                disabled=True
            )

    if st.button("🗑️ Clear Character"):
        st.session_state.character_summary = ""
        st.session_state.character_name = ""
        st.session_state.pdf_processed = False
        st.session_state.chat_history = []
        st.rerun()

# Main chat interface
st.header("💬 Chat Interface")

# Check if character is loaded
if not st.session_state.pdf_processed:
    st.info("👈 Please set up a character in the sidebar to start chatting!")
else:
    # Display chat history
    if st.session_state.chat_history:
        st.subheader("Chat History")
        for i, (user_msg, char_response) in enumerate(st.session_state.chat_history):
            with st.container():
                st.markdown(f"**You:** {user_msg}")
                st.markdown(f"**{st.session_state.character_name}:** {char_response}")
                st.divider()

    # Chat input
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area(
            f"Message to {st.session_state.character_name}",
            placeholder=f"Type your message to {st.session_state.character_name}...",
            height=100
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            submit_button = st.form_submit_button("Send 📤", type="primary")
        with col2:
            clear_chat = st.form_submit_button("Clear Chat 🗑️")

    # Handle chat submission
    if submit_button and user_input.strip():
        with st.spinner(f"💭 {st.session_state.character_name} is thinking..."):
            try:
                crew = build_character_crew(
                    st.session_state.character_name,
                    st.session_state.character_summary,
                    user_input,
                    groq_llm
                )

                result = crew.kickoff()

                if hasattr(result, 'raw'):
                    character_response = result.raw
                else:
                    character_response = str(result)

                st.session_state.chat_history.append((user_input, character_response))

                st.rerun()

            except Exception as e:
                st.error(f"Error getting response: {str(e)}")
                st.error("Please check your API key and try again.")

    if clear_chat:
        st.session_state.chat_history = []
        st.rerun()

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using CrewAI, LangChain, and Streamlit")