"""
FastAPI Backend for CrewAI Flowchart Generator
User submits query, receives flowchart HTML
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from crewai import Agent, Task, Crew, Process
import re
import os
import uuid
from datetime import datetime
from pyflowchart import Flowchart, output_html

# Initialize LLM
from llm import gemini_llm

# FastAPI app
app = FastAPI(
    title="Flowchart Generator API",
    description="Generate flowcharts from natural language queries using AI",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class FlowchartRequest(BaseModel):
    query: str

    class Config:
        json_schema_extra = {
            "example": {
                "query": "if a user age is more than 18 they can drive lmv and if more than 24 than hmv"
            }
        }

class FlowchartResponse(BaseModel):
    success: bool
    message: str
    flowchart_id: str
    html_url: str
    generated_code: str
    flowchart_definition: str

# Define Agents
requirements_analyzer = Agent(
    role='Requirements Analyzer',
    goal='Understand user requirements and create a detailed specification for flowchart logic',
    backstory="""You are an expert business analyst who can understand user requirements 
    and translate them into clear, detailed specifications for flowcharts. You excel at 
    identifying the core logic flow, decision points, inputs, and outputs.""",
    verbose=True,
    allow_delegation=False,
    llm=gemini_llm
)

code_generator = Agent(
    role='Flowchart Code Generator',
    goal='Generate Python code that represents logic flow for flowchart visualization',
    backstory="""You are a Python developer specializing in creating code for flowchart 
    visualization. You write clear, simple functions that show logic flow with:
    - Clear function definitions
    - Input/output operations (using variables, not actual input())
    - Decision points (if/elif/else)
    - Loops where needed
    - Comments explaining the flow
    
    IMPORTANT: The code you generate is ONLY for flowchart visualization, not execution.
    Use placeholder variables instead of input() calls.""",
    verbose=True,
    allow_delegation=False,
    llm=gemini_llm
)

flowchart_specialist = Agent(
    role='Flowchart Optimization Specialist',
    goal='Optimize code structure for clear flowchart visualization',
    backstory="""You are a flowchart expert who ensures code is perfectly structured 
    for pyflowchart conversion. You verify:
    - All decision branches are clear
    - Logic flow is easy to visualize
    - Variable names are descriptive
    - The code structure will create a clean flowchart
    
    You remove any actual execution calls and replace them with conceptual flow.""",
    verbose=True,
    allow_delegation=False,
    llm=gemini_llm
)


def create_flowchart_crew(user_query: str):
    """Create a crew that generates conceptual Python code for flowchart visualization"""

    requirements_task = Task(
        description=f"""Analyze this user request and create a flowchart specification:
        
        USER REQUEST: {user_query}
        
        Create a specification that includes:
        1. What the logic flow should represent
        2. Required inputs (as variables)
        3. Decision points (if/else conditions)
        4. Processing steps
        5. Outputs (as variable assignments or conceptual results)
        6. Any loops or iterations
        
        Focus on the LOGIC FLOW, not actual execution.""",
        agent=requirements_analyzer,
        expected_output="Detailed flowchart specification with decision points and flow"
    )

    code_task = Task(
        description="""Generate Python code that represents the logic flow for flowchart visualization.
        
        CRITICAL REQUIREMENTS:
        - Write a function that shows the logic flow
        - Use VARIABLES for inputs, NOT input() calls
        - Use clear if/elif/else for decisions
        - Use loops (for/while) where needed
        - Add comments to explain each step
        - Keep variable names descriptive
        - The code should visualize flow, not execute
        
        EXAMPLE FORMAT:
        ```python
        def check_age_logic(age):
            # Check if user is eligible
            if age >= 18:
                result = "Eligible for voting"
                if age >= 21:
                    result = "Can drive and vote"
            else:
                result = "Not eligible"
            return result
        ```
        
        Output ONLY the Python code in a code block.
        Format: ```python\n[code here]\n```""",
        agent=code_generator,
        expected_output="Conceptual Python code showing logic flow in a code block",
        context=[requirements_task]
    )

    validation_task = Task(
        description="""Review and optimize the code for flowchart visualization.
        
        Ensure:
        - All decision branches are clearly defined
        - Logic flow is sequential and clear
        - No actual execution calls (no input(), no real I/O)
        - Variable names explain the flow
        - Comments describe each decision point
        - Structure is optimal for pyflowchart
        
        Remove any:
        - Actual input() calls
        - print() statements (replace with variable assignments)
        - File operations
        - Any code that would require execution
        
        Output the final, optimized conceptual code ONLY in a code block.
        Format: ```python\n[code here]\n```""",
        agent=flowchart_specialist,
        expected_output="Optimized conceptual Python code in a code block",
        context=[code_task]
    )

    crew = Crew(
        agents=[requirements_analyzer, code_generator, flowchart_specialist],
        tasks=[requirements_task, code_task, validation_task],
        process=Process.sequential,
        verbose=True
    )

    return crew


def extract_python_code(text: str) -> str:
    """Extract Python code from crew output"""
    pattern = r'```python\s*(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)

    if matches:
        return matches[-1].strip()

    lines = text.split('\n')
    code_lines = []
    in_code = False

    for line in lines:
        if 'def ' in line or 'if ' in line or 'for ' in line or 'while ' in line:
            in_code = True
        if in_code:
            code_lines.append(line)

    if code_lines:
        return '\n'.join(code_lines)

    return text.strip()


def generate_flowchart(user_query: str, flowchart_id: str):
    """Generate flowchart from user query"""

    # Create output directory if it doesn't exist
    os.makedirs("generated_flowcharts", exist_ok=True)

    # Step 1: Generate conceptual code
    crew = create_flowchart_crew(user_query)
    result = crew.kickoff()

    # Extract the generated code
    generated_code = extract_python_code(str(result))

    # Step 2: Generate flowchart
    fc = Flowchart.from_code(generated_code)
    flowchart_code = fc.flowchart()

    # Step 3: Generate HTML
    output_file = f"generated_flowcharts/{flowchart_id}.html"
    output_html(
        output_name=output_file,
        field_name=f"flowchart_{flowchart_id}",
        flowchart=flowchart_code
    )

    return {
        'html_file': output_file,
        'generated_code': generated_code,
        'flowchart_definition': flowchart_code
    }


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Flowchart Generator API",
        "version": "1.0.0",
        "endpoints": {
            "POST /generate": "Generate flowchart from query",
            "GET /flowchart/{flowchart_id}": "View generated flowchart",
            "GET /health": "Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/generate", response_model=FlowchartResponse)
async def generate_flowchart_endpoint(request: FlowchartRequest):
    """
    Generate a flowchart from a natural language query

    - **query**: Natural language description of the logic flow

    Returns flowchart HTML, generated code, and flowchart definition
    """
    try:
        # Validate input
        if not request.query or len(request.query.strip()) == 0:
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        if len(request.query) > 2000:
            raise HTTPException(status_code=400, detail="Query too long (max 2000 characters)")

        # Generate unique ID
        flowchart_id = f"fc_{uuid.uuid4().hex[:12]}"

        print(f"\n🚀 Processing request: {flowchart_id}")
        print(f"📝 Query: {request.query}")

        # Generate flowchart
        result = generate_flowchart(request.query, flowchart_id)

        print(f"✅ Flowchart generated successfully: {flowchart_id}")

        return FlowchartResponse(
            success=True,
            message="Flowchart generated successfully",
            flowchart_id=flowchart_id,
            html_url=f"/flowchart/{flowchart_id}",
            generated_code=result['generated_code'],
            flowchart_definition=result['flowchart_definition']
        )

    except Exception as e:
        print(f"❌ Error generating flowchart: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating flowchart: {str(e)}")


@app.get("/flowchart/{flowchart_id}", response_class=HTMLResponse)
async def get_flowchart(flowchart_id: str):
    """
    Retrieve and display a generated flowchart

    - **flowchart_id**: ID of the generated flowchart
    """
    try:
        file_path = f"generated_flowcharts/{flowchart_id}.html"

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Flowchart not found")

        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        return HTMLResponse(content=html_content)

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Flowchart not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving flowchart: {str(e)}")


@app.get("/download/{flowchart_id}")
async def download_flowchart(flowchart_id: str):
    """
    Download flowchart HTML file

    - **flowchart_id**: ID of the generated flowchart
    """
    try:
        file_path = f"generated_flowcharts/{flowchart_id}.html"

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Flowchart not found")

        return FileResponse(
            file_path,
            media_type='text/html',
            filename=f"flowchart_{flowchart_id}.html"
        )

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Flowchart not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading flowchart: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    print("=" * 70)
    print("🚀 Starting Flowchart Generator API Server")
    print("=" * 70)
    print("📍 Server will run on: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    print("📊 ReDoc: http://localhost:8000/redoc")
    print("=" * 70)

    uvicorn.run(app, host="127.0.0.1", port=7000)