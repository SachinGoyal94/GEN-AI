import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.runnables.history import RunnableWithMessageHistory
from dotenv import load_dotenv
import tempfile
import os

load_dotenv()
os.environ["HF_TOKEN"] = os.getenv("HF_TOKEN")
os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_KEY")

embedding_model = HuggingFaceEmbeddings(model="all-MiniLM-L6-v2")
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

retriever = None
chat_history = ChatMessageHistory()


def load_uploaded_pdfs(uploaded_files):
    global retriever
    documents = []
    temp_paths = []

    for file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file.read())
            temp_paths.append(tmp.name)

    for path in temp_paths:
        loader = PyPDFLoader(path)
        documents.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=300)
    splits = splitter.split_documents(documents)

    vs = Chroma.from_documents(documents=splits, embedding=embedding_model)
    retriever = vs.as_retriever()
    return len(documents)

def build_chain():
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user request, "
        "formulate a standalone question that can be understood without chat history. "
        "Do NOT answer; just reformulate if needed."
    )

    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}")
    ])

    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )

    system_prompt = (
        "🧭 You are a Policy Generation Assistant. "
        "Your job is to generate clear, structured, and realistic policy documents or procedures "
        "based on the uploaded PDFs and the described problem or scenario. "
        "If the PDFs contain relevant content, use it as reference; otherwise, rely on domain reasoning. "
        "Respond with a professional tone and structure the answer with headings, bullet points, and steps.\n\n{context}"
    )

    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}")
    ])

    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        lambda _: chat_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer"
    )

    return conversational_rag_chain


st.set_page_config(page_title="RAG Policy Generator", page_icon="📜", layout="centered")

st.title("📜 RAG-Based Policy Generator Chatbot")
st.markdown("Upload PDF documents (e.g., safety manuals, regulations, reports) and describe a problem — the assistant will generate a policy or guideline addressing it.")

uploaded_files = st.file_uploader("📂 Upload one or more PDF files", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    if st.button("⚙️ Process Documents"):
        with st.spinner("Loading and embedding documents..."):
            doc_count = load_uploaded_pdfs(uploaded_files)
        st.success(f"✅ Loaded {doc_count} document sections. You can now ask policy questions.")
        chain = build_chain()
else:
    st.warning("Please upload at least one PDF to begin.")

if retriever is not None:
    user_input = st.text_area("💬 Describe the problem or situation:", placeholder="Example: How should our mine handle a methane gas leak?")
    if st.button("🧠 Generate Policy"):
        if user_input.strip():
            with st.spinner("Generating policy..."):
                response = chain.invoke({"input": user_input})
            st.subheader("🏛️ Generated Policy:")
            st.write(response["answer"])
        else:
            st.warning("Please enter a problem description.")
