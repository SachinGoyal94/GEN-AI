# gov_tools.py
from crewai.tools import BaseTool
import pandas as pd
import os, requests
from langchain_tavily import TavilySearch
class ExcelTool(BaseTool):
    name: str = "Excel/CSV Tool"
    description: str = "Read Excel/CSV and return summary + stats."

    def _run(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            return f"File {file_path} not found."
        ext = file_path.split(".")[-1].lower()
        if ext in ("xlsx", "xls"):
            df = pd.read_excel(file_path)
        elif ext == "csv":
            df = pd.read_csv(file_path)
        else:
            return f"Unsupported file: .{ext}"
        return str(df.describe(include="all")) + "\n\nSample:\n" + str(df.head())


class DocumentTool(BaseTool):
    name: str = "Document Tool"
    description: str = "Load policy documents, books, reports (txt only in this version)."

    def _run(self, file_path: str) -> str:
        ext = file_path.split(".")[-1].lower()
        if ext == "txt":
            return open(file_path, encoding="utf-8").read()[:5000]
        return f"Unsupported doc: .{ext}"


class TavilyTool(BaseTool):
    name: str = "Tavily Search"
    description: str = "Search the internet using Tavily API via LangChain integration."

    def __init__(self):
        super().__init__()
        key = os.getenv("TAVILY_KEY")
        if not key:
            raise ValueError("❌ TAVILY_KEY not set in environment.")
        os.environ["TAVILY_API_KEY"] = key
        self.tool = TavilySearch(topic="general", max_results=5)

    def _run(self, query: str) -> str:
        try:
            response = self.tool.invoke({"query": query})
            return str(response)
        except Exception as e:
            return f"TavilyTool error: {e}"


# Instances
excel_tool = ExcelTool()
doc_tool = DocumentTool()
tavily_tool = TavilyTool()
