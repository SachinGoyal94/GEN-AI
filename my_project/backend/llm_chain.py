import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Please respond carefully."),
    ("user", "Question: {question}")
])


def get_chain(engine):
    try:
        # Groq models
        if "groq" in engine.lower() or engine.lower() == "llama3-8b-8192":
            from langchain_groq import ChatGroq
            print(f"✅ Using ChatGroq for {engine}")
            # Get API key from environment variables
            groq_api_key = os.getenv("GROQ_KEY")
            if not groq_api_key:
                raise ValueError("GROQ_API_KEY environment variable not set")
            llm = ChatGroq(
                model=engine,
                groq_api_key=groq_api_key  # Explicitly pass the API key
            )

        # Gemini models
        elif "gemini" in engine.lower():
            from langchain_google_genai import ChatGoogleGenerativeAI
            print(f"✅ Using ChatGoogleGenerativeAI for {engine}")
            llm = ChatGoogleGenerativeAI(model=engine)

        # Ollama models (local)
        elif engine.lower() == "llama3.2" or "ollama" in engine.lower():
            from langchain_ollama import ChatOllama
            print(f"✅ Using ChatOllama for {engine}")
            llm = ChatOllama(model=engine)

        else:
            available_engines = ["gemini-1.5-flash", "gemini-2.0-pro", "gemini-2.5-pro", "llama3.2",
                                 "llama3-8b-8192"]
            print(f"❌ No match found for engine: '{engine}'")
            raise ValueError(f"Unknown engine: '{engine}'. Available engines: {available_engines}")

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