import os
import chromadb
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Load environment variables
load_dotenv()

# ✅ Setup Chroma Cloud client
client = chromadb.CloudClient(
    api_key=os.getenv("CHROMA_DB"),   # Your Chroma API key
    tenant=os.getenv("CHROMA_TENANT", "default_tenant"),
    database="SIHRAG"
)

# ✅ Embedding model (with HF token if needed)
os.environ["HF_TOKEN"] = os.getenv("HF_TOKEN")
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

# ✅ Split docs (large chunks so fewer total embeddings)
splitter = RecursiveCharacterTextSplitter(chunk_size=5000, chunk_overlap=500)
splits = splitter.split_documents(documents)

# ✅ Enforce free-tier quota (max 300 embeddings)
if len(splits) > 300:
    print(f"⚠️ Too many chunks ({len(splits)}). Trimming to 300 due to free Chroma quota.")
    splits = splits[:300]

# ✅ Push to Chroma Cloud
vectordb = Chroma(
    client=client,
    collection_name="pdf_docs",
    embedding_function=embedding_model
)

vectordb.add_documents(splits)

print(f"✅ Uploaded {len(splits)} chunks to Chroma Cloud (db: SIHRAG, collection: pdf_docs)")
