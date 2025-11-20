import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
from typing import List, Dict

load_dotenv()

groq_key = os.getenv("GROQ_KEY")
os.environ["GROQ_API_KEY"] = groq_key
gemini_api_key = os.getenv("GEMINI_KEY")

# ✅ ENHANCED prompt with better conversation context
prompt_with_history = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful AI assistant with access to our conversation history. 

    IMPORTANT INSTRUCTIONS:
    - Use the conversation history to provide contextual and relevant responses
    - Reference previous messages when appropriate (e.g., "As we discussed earlier...")
    - Maintain consistency with information shared in previous exchanges
    - Build upon previous topics naturally
    - If the user refers to something from earlier, acknowledge and respond appropriately
    - Keep your responses conversational and show that you remember our chat

    The conversation history shows our previous exchanges in chronological order."""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}")
])

# Simple prompt without history (fallback)
simple_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Please respond carefully and thoughtfully."),
    ("user", "Question: {question}")
])


def format_chat_history(chat_history: List[Dict]) -> List:
    """
    Convert chat history from database format to LangChain message format.

    Args:
        chat_history: List of chat records with 'question' and 'answer' keys

    Returns:
        List of LangChain message objects in chronological order
    """
    messages = []

    print(f"🔍 Formatting {len(chat_history)} chat history entries")

    for i, chat in enumerate(chat_history):
        if chat.get('question'):
            messages.append(HumanMessage(content=chat['question']))
            print(f"  📝 Human[{i}]: {chat['question'][:50]}...")
        if chat.get('answer'):
            messages.append(AIMessage(content=chat['answer']))
            print(f"  🤖 AI[{i}]: {chat['answer'][:50]}...")

    print(f"✅ Formatted {len(messages)} total messages")
    return messages


def get_chain_with_history(engine: str):
    """
    Create a chain that can handle conversation history.
    """
    try:
        # Initialize the appropriate LLM
        if engine in ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]:
            llm = ChatGroq(model=engine, streaming=True)
        elif engine in ["gemini-2.5-flash-lite"]:
            llm = ChatGoogleGenerativeAI(model=engine, google_api_key=gemini_api_key)
        elif engine in ["llama3.2:latest", "gemma3:1b"]:
            llm = ChatOllama(model=engine)
        else:
            print(f"❌ No match found for engine: '{engine}'")
            raise ValueError(f"Unknown engine: '{engine}'.")

        # Create chain with history support
        output_parser = StrOutputParser()
        chain = prompt_with_history | llm | output_parser

        print(f"✅ History-aware chain created successfully for {engine}")
        return chain

    except ImportError as e:
        print(f"❌ Import error for {engine}: {e}")
        raise ImportError(f"Required library not installed for {engine}: {e}")
    except Exception as e:
        print(f"❌ Chain creation error for {engine}: {e}")
        raise Exception(f"Failed to create chain for {engine}: {e}")



def invoke_with_history(chain, question: str, chat_history: List[Dict]) -> str:
    """
    Invoke the chain with conversation history.

    Args:
        chain: The LangChain chain object
        question: Current user question
        chat_history: List of previous chat exchanges (in chronological order)

    Returns:
        AI response string
    """
    try:
        print(f"🚀 Invoking chain with question: {question[:100]}...")
        print(f"📚 Using {len(chat_history)} previous exchanges for context")

        # Format chat history for the chain
        formatted_history = format_chat_history(chat_history)

        print(f"🔗 Total formatted messages: {len(formatted_history)}")

        # Build the complete conversation context
        conversation_data = {
            "question": question,
            "chat_history": formatted_history
        }

        print(f"💭 Sending to AI with full context...")

        # Invoke the chain with history
        response = chain.invoke(conversation_data)

        print(f"✅ Received response: {response[:100]}...")
        return response

    except Exception as e:
        print(f"❌ Error invoking chain with history: {e}")
        print(f"🔍 Error details: {str(e)}")

        # Fallback to simple invocation without history
        try:
            print("⚠️ Falling back to simple chain without history...")

        except Exception as fallback_error:
            print(f"❌ Fallback also failed: {fallback_error}")
            raise e