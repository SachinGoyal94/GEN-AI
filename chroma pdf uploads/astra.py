import os
import uuid
from dotenv import load_dotenv
from astrapy import DataAPIClient
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ✅ Load environment variables
load_dotenv()

ASTRA_DB_ID = os.getenv("ASTRA_DB_ID")
ASTRA_DB_TOKEN = os.getenv("ASTRASIHTOKEN")
ASTRA_DB_API_ENDPOINT = f"https://{ASTRA_DB_ID}-us-east1.apps.astra.datastax.com"

# ✅ Connect to Astra
client = DataAPIClient(ASTRA_DB_TOKEN)
db = client.get_database_by_api_endpoint(ASTRA_DB_API_ENDPOINT)

# Create (or get) a collection
collection = db.get_or_create_collection("documents", dimension=384, metric="cosine")

# ✅ Embedding model
os.environ["HF_TOKEN"] = os.getenv("HF_TOKEN_RAG")
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# ✅ Load PDFs
pdf_paths = [
    "attachment_36061686899462.pdf",
    "chap14AnnualReport2025en2.pdf",
    "Pro forma COP - Open Pit.pdf",
    "sanket0404_2024.pdf",
    "wcms_162738.pdf",
    "wcms_617123.pdf"
]

documents = []
for path in pdf_paths:
    if os.path.exists(path):
        loader = PyPDFLoader(path)
        documents.extend(loader.load())
    else:
        print(f"⚠️ PDF not found: {path}")

# ✅ Split docs
splitter = RecursiveCharacterTextSplitter(chunk_size=5000, chunk_overlap=500)
splits = splitter.split_documents(documents)

# ✅ Upload embeddings
for doc in splits:
    chunk_id = str(uuid.uuid4())
    doc_name = getattr(doc, "metadata", {}).get("source", "unknown_pdf")
    chunk_text = doc.page_content
    embedding_vector = embedding_model.embed_documents([chunk_text])[0]

    collection.insert_one({
        "_id": chunk_id,
        "document_name": doc_name,
        "chunk_text": chunk_text,
        "$vector": embedding_vector
    })

print(f"✅ Uploaded {len(splits)} chunks to Astra DB collection 'documents'")
