#creating a llm for crew
import os
from dotenv import load_dotenv
load_dotenv()
from crewai import LLM
gemini_key=os.getenv("GEMINI_KEY")
gemini_llm = LLM(
    model='gemini/gemini-2.5-flash-lite-preview-06-17',
    api_key=gemini_key
)