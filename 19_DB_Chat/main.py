import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import create_engine
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
load_dotenv()
app = FastAPI(title="Database Speaks - AI SQL Assistant", version="1.0")

class ChatRequest(BaseModel):
    query: str
    mysql_host: str | None = None
    mysql_user: str | None = None
    mysql_password: str | None = None
    mysql_db: str | None = None
    mysql_port: str | None = None
os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_KEY")

try:
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
except Exception as e:
    raise RuntimeError(f"❌ Failed to initialize ChatGroq: {e}")

def configure_db(req: ChatRequest):

    required = [req.mysql_host, req.mysql_user, req.mysql_password, req.mysql_db]
    if not all(required):
        raise HTTPException(status_code=400, detail="Missing MySQL connection parameters.")
    port = req.mysql_port if req.mysql_port else "3306"
    conn_str = f"mysql+mysqlconnector://{req.mysql_user}:{req.mysql_password}@{req.mysql_host}:{port}/{req.mysql_db}"
    try:
        return SQLDatabase(create_engine(conn_str))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MySQL connection failed: {str(e)}")

def get_agent(db: SQLDatabase):
    try:
        toolkit = SQLDatabaseToolkit(db=db, llm=llm)
        agent = create_sql_agent(
            llm=llm,
            toolkit=toolkit,
            verbose=True,
            handle_parsing_errors=True,
            top_k = 20,
            max_iterations=30,
            max_execution_time=30,
            early_stopping_method="force"
        )
        return agent
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent setup failed: {str(e)}")

@app.get("/")
def root():
    return {"message": "🗣️ Welcome to Database Speaks API - FastAPI version!"}

@app.post("/chat")
def chat_with_database(req: ChatRequest):
    try:
        db = configure_db(req)
        agent = get_agent(db)
        response = agent.run(req.query)
        return {
            "status": "success",
            "query": req.query,
            "response": response
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
