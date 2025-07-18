from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_groq import ChatGroq
from langchain.chains.summarize import load_summarize_chain
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize the LLM for document processing
groq_api_key = os.getenv("GROQ_KEY")

if not groq_api_key:
    raise ValueError("GROQ_KEY not found in environment variables")

# LangChain ChatGroq for document summarization
langchain_groq_llm = ChatGroq(
    model="gemma2-9b-it",
    api_key=groq_api_key,
    temperature=0.3  # Lower temperature for more focused summaries
)

# HuggingFace embeddings setup
hf_token = os.getenv('HF_TOKEN')
if hf_token:
    os.environ['HF_TOKEN'] = hf_token

from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def load_pdf_documents(filepath: str):
    """Load documents from PDF file."""
    try:
        loader = PyPDFLoader(filepath)
        documents = loader.load()
        return documents
    except Exception as e:
        raise Exception(f"Error loading PDF: {str(e)}")


def get_character_summary(character_name: str, pdf_path: str) -> str:
    """Generate a character summary from PDF document."""
    try:
        # Load documents
        documents = load_pdf_documents(pdf_path)

        if not documents:
            return f"No content found in the PDF for {character_name}"

        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )

        chunks = text_splitter.split_documents(documents)

        if not chunks:
            return f"No text chunks created from the PDF for {character_name}"

        # Create summarization chain
        summarize_chain = load_summarize_chain(
            llm=langchain_groq_llm,
            chain_type="map_reduce",
            verbose=True
        )

        # Generate summary
        summary = summarize_chain.run(chunks)

        # Create character-focused summary
        character_summary = f"""
        Character Profile for {character_name}:

        {summary}

        This character analysis should be used to understand {character_name}'s personality, 
        speaking style, motivations, and typical behavioral patterns for authentic roleplay.
        """

        return character_summary

    except Exception as e:
        error_msg = f"Error generating character summary for {character_name}: {str(e)}"
        print(error_msg)
        return error_msg