from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Type
import os
from dotenv import load_dotenv

from crewai import LLM, Agent, Task, Crew
from crewai.tools import BaseTool

from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_KEY")

if not GEMINI_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found. Please add it to your .env file.")

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Persona Flow", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_current_character_summary = ""
_current_character_name = ""

def set_character_context(character_name: str, summary: str):
    global _current_character_summary, _current_character_name
    _current_character_summary = summary
    _current_character_name = character_name

class CharacterToolInput(BaseModel):
    query: str = Field(..., description="A query about the character’s personality or behavior")


class CharacterTool(BaseTool):
    name: str = "Character Information Tool"
    description: str = "Provides character traits and background."
    args_schema: Type[BaseModel] = CharacterToolInput

    def _run(self, query: str) -> str:
        if _current_character_summary and _current_character_name:
            return (
                f"Character: {_current_character_name}\n\n"
                f"Summary: {_current_character_summary}\n\n"
                f"For your query '{query}', respond as {_current_character_name}."
            )
        else:
            return f"No active character context. Please initialize a character first."

character_tool = CharacterTool()

# ====================== CHARACTER RESPONSE TASK ======================

def create_character_response_task(character_name: str, user_message: str, agent):
    """CrewAI task for generating a character-authentic response."""
    return Task(
        description=f"""
        You are {character_name}. The user said: "{user_message}".

        Respond naturally and authentically as {character_name}.
        Maintain tone, vocabulary, and personality.
        Use Character Information Tool if needed.
        """,
        expected_output=f"An authentic, conversational reply from {character_name}.",
        tools=[character_tool],
        agent=agent
    )

# ====================== LLM INITIALIZATION ======================

# CrewAI-compatible Gemini LLM
gemini_llm = LLM(
    model="gemini/gemini-2.0-flash-lite",
    api_key=GEMINI_KEY,
    temperature=0.7
)

# LangChain Gemini model (for summary generation)
gemini_chat_llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite",
    google_api_key=GEMINI_KEY,
    temperature=0.4
)

# ====================== CHARACTER SUMMARY GENERATION ======================

def generate_character_summary(character_name: str) -> str:
    """Generate a brief character summary directly using Gemini."""
    prompt = f"""
    Provide a concise but detailed profile of {character_name} including:
    - Personality traits
    - Speaking style
    - Core motivations
    - Typical tone and mindset when speaking

    Keep it under 200 words. Write in natural language.
    """

    try:
        response = gemini_chat_llm.invoke(prompt)
        return f"""
        Character Profile for {character_name}:

        {response.content}

        Use this profile to understand {character_name}'s personality, tone, and behavior.
        """
    except Exception as e:
        return f"Error generating character summary: {str(e)}"

# ====================== CHARACTER AGENT ======================

def create_character_agent(character_name: str, character_summary: str, llm):
    """Create CrewAI agent for character."""
    return Agent(
        name=f"{character_name} Character Agent",
        role=f"Roleplay specialist for {character_name}",
        goal=f"Reply authentically as {character_name}, maintaining tone and style.",
        backstory=f"""
        You are {character_name}. Background details:

        {character_summary}

        Always respond exactly how {character_name} would — consistent tone and vocabulary.
        """,
        tools=[character_tool],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        memory=False,
        max_iter=3
    )

# ====================== FASTAPI BACKEND ======================

app = FastAPI(title="Character Chat (Gemini Backend)", version="3.0")

CHARACTER_CONTEXT = {"name": None, "summary": None, "agent": None}


@app.get("/")
def root():
    return {"message": "Character Chat Backend (Gemini) is running successfully!"}


@app.post("/set_character/")
async def set_character(character_name: str = Form(...)):
    """
    Initialize a character directly by name (no PDF upload).
    Generates a summary automatically and prepares the agent.
    """
    try:
        summary = generate_character_summary(character_name)
        set_character_context(character_name, summary)
        agent = create_character_agent(character_name, summary, gemini_llm)
        CHARACTER_CONTEXT.update({"name": character_name, "summary": summary, "agent": agent})

        return {"message": f"Character '{character_name}' initialized successfully.", "summary": summary}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/chat/")
async def chat_with_character(user_message: str = Form(...)):
    """
    Chat with the currently active character.
    """
    try:
        if not CHARACTER_CONTEXT["agent"]:
            return JSONResponse(
                status_code=400,
                content={"error": "No character initialized. Use /set_character first."}
            )

        character_name = CHARACTER_CONTEXT["name"]
        agent = CHARACTER_CONTEXT["agent"]

        # Create CrewAI task & crew
        task = create_character_response_task(character_name, user_message, agent)
        crew = Crew(agents=[agent], tasks=[task])

        # Run CrewAI task
        result = crew.kickoff()
        print (result)

        return JSONResponse(content={"response": str(result)})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Character Chat Backend (Gemini)...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
