import os
from dotenv import load_dotenv
load_dotenv()
from crewai import LLM
gemini_key=os.getenv("GEMINI_KEY")
gemini_llm = LLM(
    model='gemini/gemini-2.0-flash',
    api_key=gemini_key
)