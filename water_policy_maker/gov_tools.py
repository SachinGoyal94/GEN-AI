# gov_tools.py
from crewai.tools import BaseTool
import pandas as pd
import os

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

excel_tool = ExcelTool()
doc_tool = DocumentTool()
