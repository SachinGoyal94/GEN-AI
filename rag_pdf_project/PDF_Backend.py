from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
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
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()
app = FastAPI(title="⛑️ Mine Survival Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.environ["HF_TOKEN"]=os.getenv("HF_TOKEN_SIH")
os.environ["GOOGLE_API_KEY"]=os.getenv("GEMINI_KEY_RAG")

embedding_model = HuggingFaceEmbeddings(model="all-MiniLM-L6-v2")
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

vectorstores = {}
chat_histories = {}

pdf_paths = ["attachment_36061686899462.pdf","chap14AnnualReport2025en2.pdf","Pro forma COP - Open Pit.pdf","sanket0404_2024.pdf","wcms_162738.pdf","wcms_617123.pdf"]
documents = []

for path in pdf_paths:
    if os.path.exists(path):
        loader = PyPDFLoader(path)
        documents.extend(loader.load())
    else:
        print(f"⚠️ PDF not found: {path}")

if documents:
    splitter = RecursiveCharacterTextSplitter(chunk_size=5000, chunk_overlap=500)
    splits = splitter.split_documents(documents)
    vs = Chroma.from_documents(documents=splits, embedding=embedding_model)

    session_id = "default"
    vectorstores[session_id] = vs.as_retriever()
    chat_histories[session_id] = ChatMessageHistory()
    print(f"✅ Preloaded {len(pdf_paths)} PDFs into session '{session_id}'")
else:
    print("⚠️ No PDFs loaded. Make sure your files are in the docs/ folder.")

class AskRequest(BaseModel):
    session_id: str
    question: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ask")
async def ask_question(req: AskRequest):
    session_id = req.session_id
    question = req.question

    if session_id not in vectorstores:
        return JSONResponse(
            {"error": f"No documents available for session '{session_id}'"},
            status_code=400,
        )

    retriever = vectorstores[session_id]

    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question, "
        "formulate a standalone question which can be understood without the chat history. "
        "Do NOT answer the question, just reformulate it if needed."
    )
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [("system", contextualize_q_system_prompt),
         MessagesPlaceholder("chat_history"),
         ("human", "{input}")]
    )
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )

    system_prompt = (
        "⚠️ You are a Mine Disaster Survival Assistant. "
        "Always respond with clear, step-by-step survival guidance for trapped miners. "
        "If documents are available, use them. If not, rely on your general knowledge of mine safety. "
        "Format answers as a numbered list of survival steps.\n\n{context}"
    )
    qa_prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt),
         MessagesPlaceholder("chat_history"),
         ("human", "{input}")]
    )

    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    def get_session_history(_):
        return chat_histories[session_id]

    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain, get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer"
    )

    resp = conversational_rag_chain.invoke(
        {"input": question},
        config={"configurable": {"session_id": session_id}}
    )
    return {"answer": resp["answer"]}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)