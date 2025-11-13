from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from crewai import LLM, Agent, Task,Crew
from crewai.tools import BaseTool

from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import UnstructuredURLLoader
from langchain.chains.summarize import load_summarize_chain
from langchain.schema import Document
from youtube_transcript_api import YouTubeTranscriptApi
import requests
import os
import uvicorn
import datetime
from dotenv import load_dotenv
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

app = FastAPI(title="AI Summarizer + Blog Writer API", version="2.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_KEY)
crewai_llm = LLM(model="gemini/gemini-2.0-flash", api_key=GEMINI_KEY)

def extract_youtube_id(url: str) -> str:
    if "v=" in url:
        return url.split("v=")[-1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[-1]
    else:
        raise ValueError("Invalid YouTube URL")

def summarize_youtube(url: str, selected_lang: str) -> str:
    try:
        video_id = extract_youtube_id(url)
        rapidapi_url = "https://youtube-transcripts.p.rapidapi.com/youtube/transcript"
        querystring = {
            "url": url,
            "videoId": video_id,
            "chunkSize": "500",
            "text": "false",
            "lang": selected_lang
        }
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": "youtube-transcripts.p.rapidapi.com"
        }

        response = requests.get(rapidapi_url, headers=headers, params=querystring)
        response.raise_for_status()
        transcript_data = response.json()

        if isinstance(transcript_data, dict) and 'content' in transcript_data:
            all_texts = [item['text'] for item in transcript_data['content']]
        elif isinstance(transcript_data, list):
            all_texts = [item['text'] for item in transcript_data]
        else:
            raise Exception("Unexpected transcript format")

        text = " ".join(all_texts)
    except Exception as e:
        raise Exception(f"Failed to get YouTube transcript: {e}")

    docs = [Document(page_content=text)]
    prompt_template = """
    Provide a comprehensive and well-structured summary for the given content (~300 words).
    Include key points, main arguments, and important insights.

    Content: {text}

    Summary:
    """
    prompt = PromptTemplate(input_variables=["text"], template=prompt_template)
    chain = load_summarize_chain(llm, chain_type="stuff", prompt=prompt)
    summary = chain.run(docs)
    return summary.strip()


def summarize_web(url: str) -> str:
    try:
        loader = UnstructuredURLLoader(
            urls=[url],
            ssl_verify=False,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_1)"
            }
        )
        docs = loader.load()
        text = " ".join([d.page_content for d in docs])
    except Exception as e:
        raise Exception(f"Failed to load webpage: {e}")

    docs = [Document(page_content=text)]
    prompt_template = """
    Provide a comprehensive and well-structured summary for the given content (~300 words).
    Include key points, main arguments, and important insights.

    Content: {text}

    Summary:
    """
    prompt = PromptTemplate(input_variables=["text"], template=prompt_template)
    chain = load_summarize_chain(llm, chain_type="stuff", prompt=prompt)
    summary = chain.run(docs)
    return summary.strip()

blog_writer=Agent(
    role="Blog writer",
    goal=f"Narrate compelling tech stories from a yt video or from the web ",
    verbose=True,
    memory=True,
    backstory=(
            "With a flair for simplifying complex topics, you craft"
            "engaging narratives that captivate and educate, bringing new"
            "discoveries to light in an accessible manner."
        ),
    tools=[],
    allow_delegation=False,
    llm=crewai_llm
)


@app.get("/")
def home():
    return {"message": "AI Summarizer + Blog Writer Backend Running 🚀"}

@app.get("/summarize/youtube")
async def summarize_youtube_api(url: str = Query(...), lang: str = Query("en")):
    try:
        result = summarize_youtube(url, lang)
        return {"type": "youtube", "language": lang, "summary": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/summarize/web")
async def summarize_web_api(url: str = Query(...)):
    try:
        result = summarize_web(url)
        return {"type": "web", "summary": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/generate-blog/youtube")
async def generate_blog_from_youtube(
    url: str = Query(...),
    lang: str = Query("en"),
    summary: str = Query(None)  # optional
):
    try:
        # Use passed summary if available, else generate
        if summary is None:
            summary = summarize_youtube(url, lang)

        yt_write_task = Task(
            description=f"given a summary {summary}.",
            expected_output=f'using the info from the {summary} create the content for the blog',
            tools=[],
            agent=blog_writer,
            async_execution=False
        )

        crew = Crew(agents=[blog_writer], tasks=[yt_write_task])
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
        return {
            "response": response_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/generate-blog/web")
async def generate_blog_from_web(url: str = Query(...),summary: str = Query(None)):
    try:
        if summary is None:
            summary = summarize_web(url)
        web_write_task = Task(
            description=(
                f"given a summary {summary}."
            ),
            expected_output=f'using the info from the {summary} create the content for the blog',
            tools=[],
            agent=blog_writer,
            async_execution=False,
        )
        crew = Crew(agents=[blog_writer], tasks=[web_write_task])
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
        return {
            "response": response_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
