import streamlit as st

# Title
st.set_page_config(page_title="Markdown Viewer", layout="wide")
st.title("📄 Markdown Viewer Web App")

# File uploader
uploaded_file = st.file_uploader("Upload a .md file", type=["md", "markdown"])

# If file is uploaded, display it
if uploaded_file is not None:
    content = uploaded_file.read().decode("utf-8")
    st.markdown(content, unsafe_allow_html=True)
else:
    st.info("👈 Upload a Markdown (.md) file to view its content here.")
