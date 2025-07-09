import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
load_dotenv()

groq_key=os.getenv("GROQ_KEY")
os.environ["GROQ_API_KEY"] = groq_key
gemini_key=os.getenv("GEMINI_KEY")
os.environ["GEMINI_API_KEY"] = gemini_key

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Please respond carefully."),
    ("user", "Question: {question}")
])


def get_chain(engine):
    try:
        if engine in ["gemma2-9b-it","llama-3.1-8b-instant","llama3-8b-8192"]:
            llm = ChatGroq(model=engine,streaming=True)
        # Gemini models
        elif engine in ["gemini-1.5-flash","gemini-2.0-pro","gemini-2.5-pro"]:
            llm = ChatGoogleGenerativeAI(model=engine)
        # Ollama models (local)
        elif engine in ["llama3.2:latest","gemma3:1b"]:
            llm = ChatOllama(model=engine)
        else:
            print(f"❌ No match found for engine: '{engine}'")
            raise ValueError(f"Unknown engine: '{engine}'.")

        output_parser = StrOutputParser()
        chain = prompt | llm | output_parser
        print(f"✅ Chain created successfully for {engine}")
        return chain

    except ImportError as e:
        print(f"❌ Import error for {engine}: {e}")
        raise ImportError(f"Required library not installed for {engine}: {e}")
    except Exception as e:
        print(f"❌ Chain creation error for {engine}: {e}")
        raise Exception(f"Failed to create chain for {engine}: {e}")