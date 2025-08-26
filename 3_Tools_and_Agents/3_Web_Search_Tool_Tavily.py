import os
from dotenv import load_dotenv

load_dotenv()
from langchain_tavily import TavilySearch
os.environ["TAVILY_API_KEY"]=os.getenv("TAVILY_KEY")
tool=TavilySearch(topic='general',max_results=5)
response=tool.invoke({"query": "who is the creator of this app https://my-ai-mitra.streamlit.app/"})
print(response)