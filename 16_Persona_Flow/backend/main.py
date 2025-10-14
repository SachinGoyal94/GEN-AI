from fastapi import FastAPI, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
import os
from dotenv import load_dotenv
from crewai import LLM, Agent, Task, Crew
from crewai.tools import BaseTool
from pydantic import BaseModel
from models_persona import PersonaFlow, PersonaMessage
from database_persona import SessionLocal, Base, engine
from langchain_google_genai import ChatGoogleGenerativeAI
from models_user import Users

# ================= LOAD ENVIRONMENT =================
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_KEY")
if not GEMINI_KEY:
    raise ValueError("⚠ GEMINI_KEY missing in .env file")

# ================= FASTAPI SETUP =================
app = FastAPI(title="Persona Flow Microservice", version="1.1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

Base.metadata.create_all(bind=engine)

# ================= DATABASE SESSION =================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ================= CREWAI SETUP =================
gemini_llm = LLM(
    model="gemini/gemini-2.0-flash-lite",
    api_key=GEMINI_KEY,
    temperature=0.7
)
gemini_chat_llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite",
    google_api_key=GEMINI_KEY,
    temperature=0.4
)

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
    response = gemini_chat_llm.invoke(prompt)
    return response.content


def generate_custom_character_summary(user_prompt: str, tone: str) -> str:
    prompt = f"Create a character based on: '{user_prompt}' with tone {tone}."
    response = gemini_chat_llm.invoke(prompt)
    return response.content


def create_character_agent(character_name: str, character_summary: str, llm, tone: str):
    return Agent(
        name=f"{character_name} Agent",
        role=f"Conversational agent ({tone})",
        goal=f"Reply authentically as {character_name}",
        backstory=character_summary,
        tools=[character_tool],
        llm=llm,
        verbose=True,
        memory=False,
        allow_delegation=False,
        max_iter=3
    )


# ================== ROUTES ==================

@app.get("/get_user_id/{username}")
def get_user_id(username: str, db: Session = Depends(get_db)):
    """
    Fetch user_id from shared 'users' table using username.
    """
    try:
        user = db.query(Users).filter(Users.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {"user_id": user.id, "username": user.username}

    except Exception as e:
        import traceback
        print("❌ Get User ID Error:", traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/set_character/")
def set_character(
        username: str = Form(...),
        mode: str = Form(...),  # 'auto' or 'custom'
        character_name: str = Form(...),  # REQUIRED for both modes
        custom_prompt: Optional[str] = Form(None),  # only required for custom mode
        tone: str = Form("neutral"),  # user can override tone
        db: Session = Depends(get_db)
):
    """
    Creates a new character persona for a user.
    """
    try:
        # Get user_id using username
        user = db.query(Users).filter(Users.username == username).first()
        if not user:
            return JSONResponse(status_code=404, content={"error": "User not found"})
        user_id = user.id

        # Validate mode
        if mode not in ["auto", "custom"]:
            return JSONResponse(status_code=400, content={"error": "Invalid mode. Must be 'auto' or 'custom'."})

        # Validate custom_prompt for custom mode
        if mode == "custom" and not custom_prompt:
            return JSONResponse(status_code=400, content={"error": "custom_prompt required for custom mode"})

        # Create persona
        persona = PersonaFlow(
            user_id=user_id,
            character_name=character_name,  # user-defined
            mode=mode,
            tone=tone,  # user-defined or default
            summary=custom_prompt if mode == "custom" else "",  # summary empty for auto mode initially
        )

        db.add(persona)
        db.commit()
        db.refresh(persona)

        return {"success": True, "character_id": persona.id, "character_name": persona.character_name,
                "tone": persona.tone}

    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/user/{user_id}/characters")
def get_user_characters(user_id: int, db: Session = Depends(get_db)):
    """
    Get all characters/personas created by a specific user.
    """
    try:
        personas = (
            db.query(PersonaFlow)
            .filter(PersonaFlow.user_id == user_id)
            .order_by(PersonaFlow.created_at.desc())
            .all()
        )

        result = []
        for persona in personas:
            message_count = db.query(PersonaMessage).filter(
                PersonaMessage.persona_id == persona.id
            ).count()

            result.append({
                "persona_id": persona.id,
                "character_name": persona.character_name,
                "mode": persona.mode,
                "tone": persona.tone,
                "summary": persona.summary,
                "created_at": persona.created_at.isoformat(),
                "message_count": message_count
            })

        return {
            "user_id": user_id,
            "total_characters": len(result),
            "characters": result
        }

    except Exception as e:
        import traceback
        print("❌ Get Characters Error:", traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/chat/")
def chat(
        user_id: int = Form(...),
        persona_id: int = Form(...),
        user_message: str = Form(...),
        max_history: int = Form(20),
        db: Session = Depends(get_db)
):
    """
    Chat with a specific persona.
    """
    try:
        persona = (
            db.query(PersonaFlow)
            .filter(PersonaFlow.id == persona_id, PersonaFlow.user_id == user_id)
            .first()
        )
        if not persona:
            return JSONResponse(status_code=404, content={"error": "Persona not found for this user"})

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
            persona.character_name, persona.summary, gemini_llm, persona.tone
        )

        full_prompt = (
            f"You are {persona.character_name}.\n"
            f"Your tone: {persona.tone}\n\n"
            f"Conversation so far:\n{context_text}\n\n"
            f"Now the user says: {user_message}\n\n"
            f"Reply as {persona.character_name}, keeping the same tone."
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

        return {
            "persona_id": persona_id,
            "character_name": persona.character_name,
            "response": response_text
        }

    except Exception as e:
        import traceback
        print("❌ Chat Error:", traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/history/{user_id}/{persona_id}")
def get_history(user_id: int, persona_id: int, db: Session = Depends(get_db)):
    """
    Fetch chat history for a persona.
    """
    try:
        persona = (
            db.query(PersonaFlow)
            .filter(PersonaFlow.id == persona_id, PersonaFlow.user_id == user_id)
            .first()
        )

        if not persona:
            return JSONResponse(status_code=404, content={"error": "Persona not found for this user"})

        msgs = (
            db.query(PersonaMessage)
            .filter(PersonaMessage.persona_id == persona_id)
            .order_by(PersonaMessage.created_at.asc())
            .all()
        )

        return {
            "persona_id": persona_id,
            "character_name": persona.character_name,
            "user_id": user_id,
            "message_count": len(msgs),
            "messages": [
                {
                    "sender": m.sender,
                    "message": m.message,
                    "created_at": m.created_at.isoformat()
                }
                for m in msgs
            ]
        }

    except Exception as e:
        import traceback
        print("❌ Get History Error:", traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.delete("/character/{persona_id}")
def delete_character(
        persona_id: int,
        user_id: int = Form(...),
        db: Session = Depends(get_db)
):
    """
    Delete a persona and its messages.
    """
    try:
        persona = (
            db.query(PersonaFlow)
            .filter(PersonaFlow.id == persona_id, PersonaFlow.user_id == user_id)
            .first()
        )

        if not persona:
            return JSONResponse(status_code=404, content={"error": "Character not found or access denied"})

        character_name = persona.character_name
        db.delete(persona)
        db.commit()

        return {
            "success": True,
            "message": f"Character '{character_name}' deleted successfully",
            "deleted_persona_id": persona_id
        }

    except Exception as e:
        import traceback
        print("❌ Delete Character Error:", traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "persona-microservice"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
