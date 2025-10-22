import os
import re
import uuid
import traceback
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pyflowchart import Flowchart, output_html
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, LLM
from fastapi.middleware.cors import CORSMiddleware
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API key
load_dotenv()
mistral_key = os.getenv("MISTRAL_KEY")

if not mistral_key:
    logger.error("MISTRAL_KEY not found in environment variables!")

# Initialize FastAPI
app = FastAPI(title="Flowchart Generator API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LLM
try:
    llm = LLM(
        model="mistral/mistral-large-latest",
        api_key=mistral_key
    )
    logger.info("LLM initialized successfully")
except Exception as e:
    logger.error(f"Error initializing LLM: {e}")
    llm = None

# Python template
python_base = "print('start') <python code> print('end')"

# Create output directory
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)
logger.info(f"Output directory: {OUTPUT_DIR.absolute()}")


class FlowchartRequest(BaseModel):
    prompt: str


class FlowchartResponse(BaseModel):
    job_id: str
    message: str
    svg_url: str
    png_url: str
    generated_code: str


def remove_code_formatting(code: str) -> str:
    """Remove markdown code blocks and triple quotes from generated code."""
    try:
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()

        code = code.strip()
        if code.startswith('"""') or code.startswith("'''"):
            code = code[3:]
        if code.endswith('"""') or code.endswith("'''"):
            code = code[:-3]

        return code.strip()
    except Exception as e:
        logger.error(f"Error in remove_code_formatting: {e}")
        return code


def generate_python_code(user_prompt: str) -> str:
    logger.info(f"Generating code for prompt: {user_prompt}")
    try:
        # CrewAI agent to generate Python code
        code_generator = Agent(
            role="Python Flowchart Code Generator",
            goal="Generate Python code for a flowchart based on user requests.",
            backstory="An expert programmer who writes concise Python functions/classes suitable for flowchart visualization.",
            llm=llm
        )

        task = Task(
            description=f"Generate Python code for this request: {user_prompt} using python template:\n{python_base}\nDo not include anything unsafe or invalid. Return only pure Python code without markdown formatting or triple quotes.",
            expected_output="Valid Python code ready for flowchart generation.",
            agent=code_generator
        )
        crew = Crew(
            agents=[code_generator],
            tasks=[task],
            verbose=True
        )
        result = crew.kickoff()
        code = result.raw.strip()
        code = remove_code_formatting(code)
        logger.info(f"Generated code:\n{code}")
        return code
    except Exception as e:
        logger.error(f"Error generating code: {e}\n{traceback.format_exc()}")
        raise


def clean_python_code(code: str) -> str:
    logger.info("Cleaning Python code...")
    try:
        code = remove_code_formatting(code)

        # CrewAI agent to clean/fix Python code
        code_cleaner = Agent(
            role="Python Code Cleaner",
            goal="Analyze Python code, remove or fix parts that can cause runtime or syntax errors, and return safe code for flowchart generation.",
            backstory="An expert Python developer who ensures that any generated code is syntactically correct and safe to execute for visualization.",
            llm=llm
        )

        task = Task(
            description=f"Clean and fix this Python code to remove errors and make it safe for flowchart generation:\n{code}\nReturn only pure Python code without markdown formatting or triple quotes.",
            expected_output="Error-free Python code ready for flowchart visualization.",
            agent=code_cleaner
        )
        crew = Crew(
            agents=[code_cleaner],
            tasks=[task],
            verbose=True
        )
        result = crew.kickoff()
        cleaned_code = result.raw.strip()
        cleaned_code = remove_code_formatting(cleaned_code)
        logger.info(f"Cleaned code:\n{cleaned_code}")
        return cleaned_code
    except Exception as e:
        logger.error(f"Error cleaning code: {e}\n{traceback.format_exc()}")
        # Return original code if cleaning fails
        return code


def detect_first_function(code: str) -> str:
    try:
        match = re.search(r'def (\w+)\s*\(', code)
        if match:
            func_name = match.group(1)
            logger.info(f"Detected function: {func_name}")
            return func_name
        else:
            logger.warning("No function detected, using 'main'")
            return "main"
    except Exception as e:
        logger.error(f"Error detecting function: {e}")
        return "main"


def generate_flowchart_html(code: str, field_name: str, html_filename: str):
    logger.info(f"Generating flowchart HTML for function: {field_name}")
    try:
        fc = Flowchart.from_code(code, field=field_name, inner=False)
        flowchart_str = fc.flowchart()
        output_html(html_filename, field_name, flowchart_str)
        logger.info(f"HTML generated: {html_filename}")
        return html_filename, flowchart_str
    except Exception as e:
        logger.error(f"Error generating flowchart HTML: {e}\n{traceback.format_exc()}")
        raise


def render_and_download_selenium(html_file: str, svg_content: str, png_file: str, svg_file: str):
    """Use Selenium to render HTML to PNG"""
    logger.info("Starting render with Selenium...")
    driver = None
    try:
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")

        # Initialize Chrome driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Load HTML and take screenshot
        abs_path = f"file:///{os.path.abspath(html_file).replace(os.sep, '/')}"
        logger.info(f"Loading HTML from: {abs_path}")
        driver.get(abs_path)

        # Wait for SVG to load
        import time
        time.sleep(2)

        # Find SVG element and take screenshot
        try:
            svg_element = driver.find_element("tag name", "svg")
            svg_element.screenshot(png_file)
            logger.info(f"PNG saved: {png_file}")
        except Exception as e:
            logger.warning(f"Could not screenshot SVG element: {e}, taking full page screenshot")
            driver.save_screenshot(png_file)
            logger.info(f"Full page PNG saved: {png_file}")

        # Save SVG file
        with open(svg_file, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        logger.info(f"SVG saved: {svg_file}")

    except Exception as e:
        logger.error(f"Error in render_and_download_selenium: {e}\n{traceback.format_exc()}")
        raise
    finally:
        if driver:
            driver.quit()


def generate_flowchart_from_prompt(user_prompt: str, job_id: str):
    logger.info(f"Starting flowchart generation for job: {job_id}")
    try:
        # Generate filenames
        html_file = OUTPUT_DIR / f"{job_id}.html"
        png_file = OUTPUT_DIR / f"{job_id}.png"
        svg_file = OUTPUT_DIR / f"{job_id}.svg"

        # Step 1: Generate code
        python_code = generate_python_code(user_prompt)

        # Step 2: Clean/fix code
        cleaned_code = clean_python_code(python_code)

        # Step 3: Detect function
        function_name = detect_first_function(cleaned_code)

        # Step 4: Generate HTML and get SVG content
        html_file_path, svg_content = generate_flowchart_html(cleaned_code, function_name, str(html_file))

        # Step 5: Render PNG and save SVG using Selenium
        render_and_download_selenium(str(html_file), svg_content, str(png_file), str(svg_file))

        logger.info(f"Flowchart generation completed for job: {job_id}")
        return cleaned_code
    except Exception as e:
        logger.error(f"Error in generate_flowchart_from_prompt: {e}\n{traceback.format_exc()}")
        raise


@app.get("/")
async def root():
    return {
        "message": "Flowchart Generator API",
        "version": "1.0.0",
        "status": "operational" if llm else "llm_not_initialized",
        "endpoints": {
            "POST /generate": "Generate flowchart from prompt",
            "GET /download/svg/{job_id}": "Download SVG file",
            "GET /download/png/{job_id}": "Download PNG file",
            "GET /health": "Check API health"
        }
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy" if llm else "unhealthy",
        "llm_initialized": llm is not None,
        "output_dir": str(OUTPUT_DIR.absolute()),
        "output_dir_exists": OUTPUT_DIR.exists()
    }


@app.post("/generate", response_model=FlowchartResponse)
async def generate_flowchart(request: FlowchartRequest, background_tasks: BackgroundTasks):
    """
    Generate a flowchart from a text prompt.

    Example request:
    {
        "prompt": "create a flowchart for age-based vehicle selection"
    }
    """
    logger.info(f"Received generate request: {request.prompt}")

    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        logger.info(f"Generated job_id: {job_id}")

        # Generate flowchart (synchronous since Selenium doesn't need async)
        generated_code = generate_flowchart_from_prompt(request.prompt, job_id)

        return FlowchartResponse(
            job_id=job_id,
            message="Flowchart generated successfully",
            svg_url=f"/download/svg/{job_id}",
            png_url=f"/download/png/{job_id}",
            generated_code=generated_code
        )
    except Exception as e:
        logger.error(f"Error in generate_flowchart endpoint: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )


@app.get("/download/svg/{job_id}")
async def download_svg(job_id: str):
    """Download the generated SVG file"""
    svg_file = OUTPUT_DIR / f"{job_id}.svg"

    if not svg_file.exists():
        logger.error(f"SVG file not found: {svg_file}")
        raise HTTPException(status_code=404, detail="SVG file not found")

    return FileResponse(
        path=svg_file,
        media_type="image/svg+xml",
        filename=f"flowchart_{job_id}.svg"
    )


@app.get("/download/png/{job_id}")
async def download_png(job_id: str):
    """Download the generated PNG file"""
    png_file = OUTPUT_DIR / f"{job_id}.png"

    if not png_file.exists():
        logger.error(f"PNG file not found: {png_file}")
        raise HTTPException(status_code=404, detail="PNG file not found")

    return FileResponse(
        path=png_file,
        media_type="image/png",
        filename=f"flowchart_{job_id}.png"
    )


@app.delete("/cleanup/{job_id}")
async def cleanup_files(job_id: str):
    """Delete generated files for a job"""
    deleted = []
    for ext in ['.html', '.svg', '.png']:
        file_path = OUTPUT_DIR / f"{job_id}{ext}"
        if file_path.exists():
            file_path.unlink()
            deleted.append(str(file_path))

    return {"message": "Files cleaned up", "deleted_files": deleted}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
