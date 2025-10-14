from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from summarizer import summarize_youtube, summarize_web
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI Summarizer API", version="1.1")

# Allow frontend (Streamlit or React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "AI Summarizer Backend is running 🚀"}

@app.get("/summarize/youtube")
async def summarize_youtube_api(
    url: str = Query(..., description="YouTube video URL"),
    lang: str = Query("en", description="Language code for transcript (e.g., en, hi, es)")
):
    """
    Summarize a YouTube video transcript in the selected language.
    Default language: English (en)
    """
    try:
        result = summarize_youtube(url, lang)
        return {"type": "youtube", "language": lang, "summary": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/summarize/web")
async def summarize_web_api(
    url: str = Query(..., description="Website URL")
):
    try:
        result = summarize_web(url)
        return {"type": "web", "summary": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
