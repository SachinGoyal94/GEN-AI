import os
from crewai import Agent, LLM
from dotenv import load_dotenv

load_dotenv()

llm = LLM(model="gemini/gemini-2.5-flash-lite-preview-06-17", api_key=os.getenv("GEMINI_KEY"))

# 🧠 Analyzer Agent
analyzer_agent = Agent(
    role="Logic Analyzer",
    goal="Analyze the input code or text and extract the main logical flow.",
    backstory="You are skilled at breaking down logic into steps and decisions.",
    llm=llm,
)

# 🎨 Designer Agent
designer_agent = Agent(
    role="Flowchart Designer",
    goal="Convert extracted logic into valid Mermaid flowchart syntax.",
    backstory=(
        "You are a flowchart design expert. "
        "You use 'flowchart TD' or 'flowchart LR' syntax with nodes like A[Start], B{Condition}, etc."
    ),
    llm=llm,
)

# 🧱 Renderer Agent
renderer_agent = Agent(
    role="HTML Renderer",
    goal="Wrap the Mermaid flowchart in an HTML structure with mermaid.js for rendering.",
    backstory="You are a frontend developer skilled at embedding Mermaid diagrams into HTML pages.",
    llm=llm,
)
