from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal, Base, engine
from models import User, ChatHistory
from llm_chain import get_chain_with_history, invoke_with_history
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_password_hash(password: str):
    # Encode and truncate to 72 bytes (bcrypt limit)
    return pwd_context.hash(password.encode('utf-8')[:72])


def verify_password(plain_password: str, hashed_password: str):
    # Apply same truncation during verification
    return pwd_context.verify(plain_password.encode('utf-8')[:72], hashed_password)



def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


class RegisterUser(BaseModel):
    username: str
    password: str


@app.post("/register")
def register(user: RegisterUser, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed_pw = get_password_hash(user.password)
    new_user = User(username=user.username, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    return {"message": "Registered successfully"}


@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}


class AskPrompt(BaseModel):
    question: str
    engine: str
    use_history: Optional[bool] = True
    max_history: Optional[int] = 10


@app.post("/ask")
def ask(req: AskPrompt, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        print(f"🚩 Received engine: '{req.engine}'")
        print(f"📚 Use history: {req.use_history}")
        print(f"👤 User ID: {user.id}")

        if req.use_history:
            chat_history_records = (
                db.query(ChatHistory)
                .filter(ChatHistory.user_id == user.id)
                .order_by(ChatHistory.created_at.asc())  # ✅ OLDEST FIRST
                .all()
            )

            recent_records = chat_history_records[-(req.max_history or 10):] if len(chat_history_records) > (req.max_history or 10) else chat_history_records

            chat_history = [
                {"question": record.question, "answer": record.answer}
                for record in recent_records
            ]

            print(f"📖 Retrieved {len(chat_history)} previous chat exchanges")
            print(f"📝 Chat history preview: {chat_history[-2:] if chat_history else 'No history'}")

            chain = get_chain_with_history(req.engine)

            answer = invoke_with_history(chain, req.question, chat_history)

        else:
            print("🔥 Using simple chain without history")

        chat = ChatHistory(
            user_id=user.id,
            question=req.question,
            answer=answer
        )
        db.add(chat)
        db.commit()
        print(f"💾 Saved new chat to database")

        return {"answer": answer, "used_history": req.use_history}

    except Exception as e:
        print(f"❌ Error in ask endpoint: {str(e)}")
        import traceback
        print(f"🔍 Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process request: {str(e)}"
        )


@app.get("/history")
def history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    chats = (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == user.id)
        .order_by(ChatHistory.created_at.desc())
        .all()
    )
    return [
        {
            "id": c.id,
            "question": c.question,
            "answer": c.answer,
            "created_at": c.created_at.isoformat()
        }
        for c in chats
    ]


@app.delete("/history")
def delete_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    deleted_count = db.query(ChatHistory).filter(ChatHistory.user_id == user.id).delete()
    db.commit()
    return {"message": f"Chat history cleared ({deleted_count} messages deleted)"}


@app.get("/history/count")
def history_count(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    count = db.query(ChatHistory).filter(ChatHistory.user_id == user.id).count()
    return {"count": count}


@app.delete("/history/{chat_id}")
def delete_specific_chat(chat_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    chat = (
        db.query(ChatHistory)
        .filter(ChatHistory.id == chat_id, ChatHistory.user_id == user.id)
        .first()
    )

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    db.delete(chat)
    db.commit()
    return {"message": "Chat deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)