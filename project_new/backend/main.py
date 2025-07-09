from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from pymongo import MongoClient
from llm_chain import get_chain
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB setup
client = MongoClient(os.getenv("MONGO_URI"))
db = client["chat_db"]
chats = db["chats"]
try:
    chats.insert_one({...})
except Exception as e:
    print(f"Skipping MongoDB insert, got error: {e}")

app = FastAPI()

class PromptRequest(BaseModel):
    user_id: str
    question: str
    engine: str

@app.post("/ask")
async def ask_question(req: PromptRequest):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_KEY")

    chain = get_chain(req.engine)
    answer = chain.invoke({"question": req.question})

    # Store in MongoDB
    #chats.insert_one({
    #    "user_id": req.user_id,
    #    "question": req.question,
    #    "answer": answer,
    #    "timestamp": datetime.utcnow()
    #})

    return {"answer": answer}
