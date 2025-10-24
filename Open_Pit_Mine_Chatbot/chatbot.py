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
import os

# 🔹 Load API keys
load_dotenv()
os.environ["HF_TOKEN"] = os.getenv("HF_TOKEN")
os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_KEY")

# 🔹 Initialize models
embedding_model = HuggingFaceEmbeddings(model="all-MiniLM-L6-v2")
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

retriever = None
chat_history = ChatMessageHistory()

# 🔹 Hardcoded PDFs
documents_files = [
    'wcms_617123.pdf',
    'wcms_162738.pdf',
    'sanket0404_2024.pdf',
    'Pro forma COP - Open Pit.pdf',
    'chap14AnnualReport2025en2.pdf',
    'attachment_36061686899462.pdf'
]

# 🔹 Load PDFs
def load_pdfs(file_paths):
    global retriever
    documents = []
    for path in file_paths:
        loader = PyPDFLoader(path)
        documents.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(chunk_size=5000, chunk_overlap=500)
    splits = splitter.split_documents(documents)

    vs = Chroma.from_documents(documents=splits, embedding=embedding_model)
    retriever = vs.as_retriever()
    print(f"✅ Loaded {len(file_paths)} PDFs into retriever.")

# 🔹 Build RAG chain
def build_chain():
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

    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain, lambda _: chat_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer"
    )
    return conversational_rag_chain

# 🔹 Predefined alerts
predefined_alerts = [
    "🚨 Mine roof collapse",
    "🔥 Fire inside the mine",
    "💨 Lack of oxygen detected",
    "🌊 Flooding in the mine tunnel",
    "⚡ Electrical equipment failure",
    "🧯 Gas leakage (methane/carbon monoxide)",
    "🚪 Blocked exit route",
    "📡 Lost communication with rescue team",
    "🤕 Miner is injured and trapped",
    "🕳️ Pit wall collapse"
]

# 🔹 Terminal CLI
if __name__ == "__main__":
    print("=== ⛑️ Mine Survival Assistant CLI ===")

    # Automatically load the hardcoded PDFs
    load_pdfs(documents_files)

    chain = build_chain()

    print("\n🚨 Select a predefined alert or type a custom one. Type 'exit' to quit.")

    while True:
        # Show predefined alerts
        print("\nPredefined Alerts:")
        for idx, alert in enumerate(predefined_alerts, start=1):
            print(f"{idx}. {alert}")
        print("0. Type your own alert/question")

        choice = input("\nSelect alert number (or 0 for custom): ").strip()

        # Allow exiting anytime
        if choice.lower() in ["exit", "quit"]:
            print("👋 Exiting...")
            break

        choice = choice.strip()
        if choice.isdigit():
            num = int(choice)
            if 1 <= num <= len(predefined_alerts):
                final_input = predefined_alerts[num-1]
            elif num == 0:
                final_input = input("Enter your custom alert/question: ").strip()
                if final_input.lower() in ["exit", "quit"]:
                    print("👋 Exiting...")
                    break
            else:
                print("❌ Invalid choice. Try again.")
                continue
        else:
            print("❌ Invalid input. Enter a number.")
            continue

        resp = chain.invoke({"input": final_input})
        print("\n🛟 Survival Guidance:\n", resp["answer"])
