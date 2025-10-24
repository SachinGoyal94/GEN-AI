import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from crewai import Task, Crew
from dotenv import load_dotenv
from agents import analyzer_agent, designer_agent, renderer_agent
from utils.mermaid_renderer import wrap_mermaid_in_html

# Load environment variables (API keys etc.)
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Agentic Flowchart Generator",
    version="1.0.1",
    description="An agentic AI system that generates flowcharts from natural language or code using multi-agent reasoning and Mermaid.js."
)

# Input schema
class FlowchartRequest(BaseModel):
    prompt: str


@app.post("/generate_flowchart")
def generate_flowchart(req: FlowchartRequest):
    """
    Endpoint to generate a flowchart HTML from user input using multi-agent CrewAI reasoning.
    """
    try:
        # -------------------------------
        # Step 1️⃣: Analyze Input
        # -------------------------------
        analyze_task = Task(
            description=f"Analyze this user input and extract clear logical steps or decision flow:\n\n{req.prompt}",
            expected_output="A numbered list or structured description of the logical steps and decisions involved in the process.",
            agent=analyzer_agent,
        )

        # -------------------------------
        # Step 2️⃣: Design Flowchart (Mermaid)
        # -------------------------------
        design_task = Task(
            description=(
                "Using the logic provided by the previous analysis, create a valid Mermaid.js flowchart. "
                "Use syntax like:\nflowchart TD\nA[Start] --> B{Condition}\nB -->|Yes| C[Action]\nB -->|No| D[Other Action]\nC --> E[End]\n"
                "Ensure the output is **only** the Mermaid code, nothing else."
            ),
            expected_output="A valid Mermaid.js flowchart code block starting with 'flowchart TD' or 'flowchart LR'.",
            agent=designer_agent,
        )

        # -------------------------------
        # Step 3️⃣: Render HTML
        # -------------------------------
        render_task = Task(
            description=(
                "Take the Mermaid.js code and wrap it into a complete HTML page "
                "that can render the diagram automatically in browsers using mermaid.js CDN."
            ),
            expected_output="A complete HTML page containing the Mermaid diagram ready for viewing.",
            agent=renderer_agent,
        )

        # -------------------------------
        # Step 4️⃣: Create Crew & Execute
        # -------------------------------
        crew = Crew(
            agents=[analyzer_agent, designer_agent, renderer_agent],
            tasks=[analyze_task, design_task, render_task],
            verbose=True,
        )

        # Run the multi-agent reasoning workflow
        result = crew.kickoff()

        # Handle cases where result is raw Mermaid code
        if "flowchart" in result and "<html" not in result:
            result = wrap_mermaid_in_html(result)

        # Return JSON with HTML embedded
        return {"html": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Optional: simple root route
@app.get("/")
def home():
    return {
        "message": "Welcome to the Agentic Flowchart Generator 🧠",
        "docs": "Visit /docs to test the API interactively.",
    }


# -------------------------------
# Run with: uvicorn main:app --reload
# -------------------------------
