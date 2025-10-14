import requests
import validators
import time

from youtube_transcript_api import YouTubeTranscriptApi
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import UnstructuredURLLoader
from langchain.chains.summarize import load_summarize_chain
from langchain.schema import Document
from dotenv import load_dotenv
import os

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite-preview-06-17", google_api_key=GEMINI_KEY)

def extract_youtube_id(url: str) -> str:
    if "v=" in url:
        return url.split("v=")[-1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[-1]
    else:
        raise ValueError("Invalid YouTube URL")


def summarize_youtube(url: str,selected_lang: str) -> str:
    try:
        video_id = extract_youtube_id(url)
        rapidapi_url = "https://youtube-transcripts.p.rapidapi.com/youtube/transcript"
        querystring = {
            "url": url,
            "videoId": video_id,
            "chunkSize": "500",
            "text": "false",  # As per user's provided example
            "lang": selected_lang
        }
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": "youtube-transcripts.p.rapidapi.com"
        }

        response = requests.get(rapidapi_url, headers=headers, params=querystring)
        response.raise_for_status()  # Raise an exception for HTTP errors
        transcript_data = response.json()

        if isinstance(transcript_data, dict) and 'content' in transcript_data:
            all_texts = [item['text'] for item in transcript_data['content']]
        elif isinstance(transcript_data, list):
            all_texts = [item['text'] for item in transcript_data]


        text = " ".join(all_texts)
    except Exception as e:
        raise Exception(f"Failed to get YouTube transcript: {e}")


    docs = [Document(page_content=text)]
    prompt_template = """
    Provide a comprehensive and well-structured summary for the given content in approximately 300 words.
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
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
            }
        )
        docs = loader.load()
        text = " ".join([d.page_content for d in docs])
    except Exception as e:
        raise Exception(f"Failed to load webpage: {e}")

    docs = [Document(page_content=text)]
    prompt_template = """
        Provide a comprehensive and well-structured summary for the given content in approximately 300 words.
        Include key points, main arguments, and important insights.

        Content: {text}

        Summary:
        """
    prompt = PromptTemplate(input_variables=["text"], template=prompt_template)
    chain = load_summarize_chain(llm, chain_type="stuff", prompt=prompt)
    summary = chain.run(docs)
    return summary.strip()
