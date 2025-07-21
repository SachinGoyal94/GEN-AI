from crewai import LLM
import os
from dotenv import load_dotenv

load_dotenv()

groq_key = os.getenv("GROQ_KEY")

if not groq_key:
    raise ValueError("GROQ_KEY not found in environment variables. Please check your .env file.")

# CrewAI LLM with Groq provider
groq_llm = LLM(
    model='groq/gemma2-9b-it',
    api_key=groq_key,
    temperature=0.7
)