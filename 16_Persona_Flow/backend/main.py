from fastapi import FastAPI, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
import os
import sys
import logging

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Create FastAPI app FIRST
app = FastAPI(title="Persona Flow Microservice", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

logger.info("✅ FastAPI app created - port will bind now")

# Now do heavy imports AFTER app is created
from dotenv import load_dotenv
from pydantic import BaseModel, Field

logger.info("🔄 Loading heavy dependencies...")

from crewai import LLM, Agent, Task, Crew
from crewai.tools import BaseTool
from models_persona import PersonaFlow, PersonaMessage
from database_persona import SessionLocal, Base, engine
from langchain_google_genai import ChatGoogleGenerativeAI

logger.info("✅ All imports loaded")

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_KEY")
if not GEMINI_KEY:
    logger.error("❌ GEMINI_KEY missing!")
    raise ValueError("❌ GEMINI_KEY missing")

logger.info("✅ GEMINI_KEY found")

Base.metadata.create_all(bind=engine)

# ================= LAZY INITIALIZATION =================
_gemini_llm = None
_gemini_chat_llm = None

def get_gemini_llm():
    global _gemini_llm
    if _gemini_llm is None:
        logger.info("🔄 Initializing Gemini LLM...")
        _gemini_llm = LLM(
            model="gemini/gemini-2.0-flash-lite",
            api_key=GEMINI_KEY,
            temperature=0.7
        )
        logger.info("✅ Gemini LLM ready")
    return _gemini_llm

def get_gemini_chat_llm():
    global _gemini_chat_llm
    if _gemini_chat_llm is None:
        logger.info("🔄 Initializing Gemini Chat LLM...")
        _gemini_chat_llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-lite",
            google_api_key=GEMINI_KEY,
            temperature=0.4
        )
        logger.info("✅ Gemini Chat LLM ready")
    return _gemini_chat_llm

# ================= DATABASE SESSION =================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ================= TOOLS =================
_current_character_summary = ""
_current_character_name = ""

def set_character_context(character_name: str, summary: str):
    global _current_character_summary, _current_character_name
    _current_character_summary = summary
    _current_character_name = character_name

class CharacterToolInput(BaseModel):
    query: str

class CharacterTool(BaseTool):
    name: str = "Character Information Tool"
    description: str = "Provides personality and behavior insights."
    args_schema: type[CharacterToolInput] = CharacterToolInput

    def _run(self, query: str) -> str:
        if _current_character_summary and _current_character_name:
            return (
                f"Character: {_current_character_name}\n"
                f"Summary: {_current_character_summary}\n"
                f"Answer for '{query}':"
            )
        return "No active character context."

character_tool = CharacterTool()

# ================== CHARACTER SUMMARY ==================
def generate_character_summary(character_name: str, tone: str) -> str:
    prompt = f"Generate a concise personality profile for {character_name} in {tone} tone."
    response = get_gemini_chat_llm().invoke(prompt)
    return response.content

def generate_custom_character_summary(user_prompt: str, tone: str) -> str:
    prompt = f"Create a character based on: '{user_prompt}' with tone {tone}."
    response = get_gemini_chat_llm().invoke(prompt)
    return response.content

def create_character_agent(character_name: str, character_summary: str, tone: str):
    return Agent(
        name=f"{character_name} Agent",
        role=f"Conversational agent ({tone})",
        goal=f"Reply authentically as {character_name}",
        backstory=character_summary,
        tools=[character_tool],
        llm=get_gemini_llm(),
        verbose=True,
        memory=False,
        allow_delegation=False,
        max_iter=3
    )

def create_character_response_task(character_name: str, user_message: str, agent, tone: str):
    return Task(
        description=f"You are {character_name}. User said: {user_message}. Respond in {tone} tone.",
        expected_output=f"{tone}-style response from {character_name}",
        tools=[character_tool],
        agent=agent
    )

# ================== ROUTES ==================
@app.get("/")
def root():
    return {"status": "ok", "service": "Persona Flow Microservice"}

@app.post("/set_character/")
def set_character(
    user_id: int = Form(...),
    mode: str = Form(...),
    character_name: Optional[str] = Form(None),
    custom_prompt: Optional[str] = Form(None),
    tone: str = Form("neutral"),
    db: Session = Depends(get_db)
):
    try:
        if mode == "auto" and not character_name:
            return JSONResponse(status_code=400, content={"error":"character_name required for auto mode"})
        if mode == "custom" and not custom_prompt:
            return JSONResponse(status_code=400, content={"error":"custom_prompt required for custom mode"})

        summary = ""
        name_to_store = character_name if mode=="auto" else "Custom Character"

        if mode == "auto":
            summary = generate_character_summary(character_name, tone)
        else:
            summary = generate_custom_character_summary(custom_prompt, tone)

        persona = PersonaFlow(
            user_id=user_id,
            character_name=name_to_store,
            mode=mode,
            tone=tone,
            summary=summary
        )
        db.add(persona)
        db.commit()
        db.refresh(persona)

        set_character_context(name_to_store, summary)
        agent = create_character_agent(name_to_store, summary, tone)
        persona.agent = agent

        return {"persona_id": persona.id, "character_name": name_to_store, "summary": summary}

    except Exception as e:
        logger.error(f"Error in set_character: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/chat/")
def chat(
    user_id: int = Form(...),
    persona_id: int = Form(...),
    user_message: str = Form(...),
    max_history: int = Form(20),
    db: Session = Depends(get_db)
):
    try:
        persona = (
            db.query(PersonaFlow)
            .filter(PersonaFlow.id == persona_id, PersonaFlow.user_id == user_id)
            .first()
        )
        if not persona:
            return JSONResponse(status_code=404, content={"error": "Persona not found for this user."})

        history_msgs = (
            db.query(PersonaMessage)
            .filter(PersonaMessage.persona_id == persona_id)
            .order_by(PersonaMessage.created_at.desc())
            .limit(max_history)
            .all()
        )

        context_text = "\n".join(
            [f"{m.sender}: {m.message}" for m in reversed(history_msgs)]
        )

        set_character_context(persona.character_name, persona.summary)
        agent = create_character_agent(
            persona.character_name, persona.summary, persona.tone
        )

        full_prompt = (
            f"You are {persona.character_name}.\n"
            f"Your tone: {persona.tone}\n\n"
            f"Conversation so far:\n{context_text}\n\n"
            f"Now the user says: {user_message}\n\n"
            f"Reply as {persona.character_name}, keeping the same tone and personality."
        )

        task = Task(
            description=full_prompt,
            expected_output=f"{persona.tone}-style response from {persona.character_name}",
            tools=[character_tool],
            agent=agent
        )

        crew = Crew(agents=[agent], tasks=[task])
        result = crew.kickoff()

        response_text = ""
        if hasattr(result, "raw") and result.raw:
            response_text = result.raw
        elif hasattr(result, "output") and result.output:
            response_text = str(result.output)
        elif hasattr(result, "results") and len(result.results) > 0:
            r = result.results[0]
            response_text = getattr(r, "raw", "") or getattr(r, "output", "")
        else:
            response_text = "No valid output from model."

        response_text = response_text.strip()

        db.add(PersonaMessage(persona_id=persona_id, sender="user", message=user_message))
        db.add(PersonaMessage(persona_id=persona_id, sender="agent", message=response_text))
        db.commit()

        return {"response": response_text}

    except Exception as e:
        import traceback
        logger.error(f"Chat Error: {traceback.format_exc()}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/history/{user_id}/{persona_id}")
def get_history(user_id: int, persona_id: int, db: Session = Depends(get_db)):
    msgs = db.query(PersonaMessage).filter(PersonaMessage.persona_id==persona_id).order_by(PersonaMessage.created_at.asc()).all()
    return [{"sender": m.sender, "message": m.message, "created_at": m.created_at.isoformat()} for m in msgs]

@app.on_event("startup")
async def startup_event():
    logger.info("🎉 Application startup complete!")
    logger.info(f"📡 Server running on port {os.getenv('PORT', 8000)}")