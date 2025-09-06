from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from tempfile import NamedTemporaryFile
from typing import Dict, Any, List
import os
from dotenv import load_dotenv

from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


SESSIONS: Dict[str, Dict[str, Any]] = {}
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    print("Warning: HF_TOKEN not set; HuggingFace embeddings may fail if missing.")
embeddings = HuggingFaceEmbeddings(model="all-MiniLM-L6-v2")

contextualize_q_system_prompt = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question; "
    "just reformulate it if needed and otherwise return it as is."
)

system_prompt = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer the question. "
    "If you don't know the answer, say that you don't know. Use three sentences maximum. "
    "\n\n{context}"
)

qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)


class LimitedChatHistory(BaseChatMessageHistory):
    def __init__(self, base_history: ChatMessageHistory, max_messages: int = 6):
        self.base = base_history
        self.max_messages = max_messages

    @property
    def messages(self):
        return self.base.messages[-self.max_messages :]

    def add_message(self, message):
        return self.base.add_message(message)

    def add_messages(self, messages):
        return self.base.add_messages(messages)


@app.post("/upload")
async def upload(
    files: List[UploadFile] = File(...),
    api_key: str = Form(...),
    session_id: str = Form(...),
):
    if session_id not in SESSIONS:
        SESSIONS[session_id] = {
            "vectorstore": None,
            "rag_chain": None,
            "llm": None,
            "history": ChatMessageHistory(),
        }

    llm = ChatGroq(groq_api_key=api_key, model_name="Gemma2-9b-It")

    docs = []
    for upload in files:
        tmp = NamedTemporaryFile(delete=False, suffix=".pdf")
        content = await upload.read()
        tmp.write(content)
        tmp.close()
        loader = PyPDFLoader(tmp.name)
        docs.extend(loader.load())

    if len(docs) == 0:
        return JSONResponse({"error": "No PDF content loaded"}, status_code=400)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    splits = text_splitter.split_documents(docs)

    # create in-memory Chroma vectorstore from splits
    vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings)

    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    SESSIONS[session_id]["vectorstore"] = vectorstore
    SESSIONS[session_id]["rag_chain"] = rag_chain
    SESSIONS[session_id]["llm"] = llm

    return JSONResponse({"detail": f"Uploaded {len(files)} file(s) and created vectorstore for session '{session_id}'"})


@app.post("/ask")
async def ask(payload: Dict[str, Any]):
    api_key = payload.get("api_key")
    session_id = payload.get("session_id", "default_session")
    question = payload.get("question")

    if not api_key or not question:
        return JSONResponse({"error": "api_key and question required"}, status_code=400)

    session = SESSIONS.get(session_id)
    if not session or session.get("rag_chain") is None:
        return JSONResponse(
            {"error": "No documents uploaded for this session. POST /upload first."}, status_code=400
        )

    rag_chain = session["rag_chain"]
    llm = session["llm"]
    base_history = session["history"]
    limited_history = LimitedChatHistory(base_history, max_messages=6)

    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        lambda s=session_id: limited_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )

    try:
        response = conversational_rag_chain.invoke(
            {"input": question}, config={"configurable": {"session_id": session_id}}
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

    base_history.add_message({"role": "user", "content": question})
    ans_text = response.get("answer") if isinstance(response, dict) else str(response)
    base_history.add_message({"role": "assistant", "content": ans_text})

    return JSONResponse({"answer": ans_text})


if __name__ == "__main__":
    import uvicorn

    #uvicorn.run(app, host="0.0.0.0", port=8000)
    uvicorn.run(app, host="0.0.0.0", port=8000)




