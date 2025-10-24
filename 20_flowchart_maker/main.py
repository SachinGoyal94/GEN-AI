import os
import re
import uuid
import traceback
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pyflowchart import Flowchart
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, LLM
from fastapi.middleware.cors import CORSMiddleware
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API key
load_dotenv()
mistral_key = os.getenv("GEMINI_KEY")

if not mistral_key:
    logger.error("MISTRAL_KEY not found in environment variables!")

# Initialize FastAPI
app = FastAPI(title="Flowchart Generator API", version="2.0.0")

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
        model="gemini/gemini-2.5-flash-lite-preview-06-17",
        api_key=mistral_key
    )
    logger.info("LLM initialized successfully")
except Exception as e:
    logger.error(f"Error initializing LLM: {e}")
    llm = None

# Python template with example
python_template = """
def process_logic():
    print('start')
    # Your logic here
    if condition:
        do_something()
    else:
        do_something_else()
    print('end')
"""

# Create output directory
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)
logger.info(f"Output directory: {OUTPUT_DIR.absolute()}")


class FlowchartRequest(BaseModel):
    prompt: str


class FlowchartResponse(BaseModel):
    job_id: str
    message: str
    view_url: str
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


def validate_code_structure(code: str) -> tuple[bool, str]:
    """Validate if code has a proper function definition."""
    if not code or len(code.strip()) == 0:
        return False, "Code is empty"

    # Check for function definition
    if not re.search(r'def\s+\w+\s*\(', code):
        return False, "No function definition found"

    # Check for basic Python syntax
    try:
        compile(code, '<string>', 'exec')
        return True, "Valid"
    except SyntaxError as e:
        return False, f"Syntax error: {str(e)}"


def wrap_code_in_function(code: str, function_name: str = "process_flowchart") -> str:
    """Wrap code that lacks a function definition in a function."""
    logger.info(f"Wrapping code in function: {function_name}")

    lines = code.split('\n')
    indented_lines = []

    for line in lines:
        if line.strip():
            indented_lines.append('    ' + line)
        else:
            indented_lines.append(line)

    wrapped_code = f"def {function_name}():\n" + '\n'.join(indented_lines)
    logger.info(f"Wrapped code:\n{wrapped_code}")
    return wrapped_code


def generate_python_code(user_prompt: str) -> str:
    logger.info(f"Generating code for prompt: {user_prompt}")
    try:
        code_generator = Agent(
            role="Flowchart Logic Designer",
            goal="Generate Python code that creates meaningful flowcharts with descriptive labels instead of code syntax.",
            backstory="An expert at designing flowcharts who uses print() statements with clear, human-readable messages to represent business logic and decision points. Avoids showing raw code in flowcharts.",
            llm=llm
        )

        task = Task(
            description=f"""Create a Python function for: {user_prompt}

CRITICAL RULES FOR FLOWCHART GENERATION:
1. Use print() statements with DESCRIPTIVE MESSAGES, not code:
   ✅ GOOD: print("Check if user age is 18 or above")
   ❌ BAD: print("if age >= 18:")

2. Every decision point should print a QUESTION:
   ✅ GOOD: print("Is the customer a premium member?")
   ❌ BAD: print("if is_premium:")

3. Every action should print what HAPPENS:
   ✅ GOOD: print("Apply 20% discount to cart")
   ❌ BAD: print("discount = 0.20")

4. Use if/else for decisions, but the print statements should describe BUSINESS LOGIC
5. Create ONE function with a descriptive name
6. No markdown, no code blocks, no explanations

EXAMPLE FOR "check voting eligibility":
```
def check_voting_eligibility():
    print("Start: Check Voting Eligibility")
    age = 18  # dummy variable
    if age >= 18:
        print("Person is 18 or older")
        print("Person is eligible to vote")
    else:
        print("Person is under 18")
        print("Person is not eligible to vote")
    print("End: Eligibility Check Complete")
```

Now generate for: {user_prompt}
Return ONLY the function code:""",
            expected_output="A Python function with descriptive print statements for flowchart visualization.",
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

        is_valid, msg = validate_code_structure(code)
        if not is_valid:
            logger.warning(f"Initial validation failed: {msg}")

        return code
    except Exception as e:
        logger.error(f"Error generating code: {e}\n{traceback.format_exc()}")
        raise


def clean_python_code(code: str) -> str:
    logger.info("Cleaning Python code...")
    try:
        code = remove_code_formatting(code)

        is_valid, msg = validate_code_structure(code)
        if not is_valid:
            logger.warning(f"Code validation failed: {msg}")

            if "No function definition found" in msg:
                logger.info("No function found, attempting to wrap code...")
                code = wrap_code_in_function(code)
                is_valid, msg = validate_code_structure(code)
                if is_valid:
                    logger.info("Successfully wrapped code in function")
                    return code

        code_cleaner = Agent(
            role="Flowchart Code Optimizer",
            goal="Ensure code has descriptive print statements for flowcharts, not raw code syntax.",
            backstory="An expert at converting code into flowchart-friendly format with human-readable messages.",
            llm=llm
        )

        task = Task(
            description=f"""Optimize this code for flowchart visualization:

{code}

REQUIREMENTS:
1. Keep the function structure intact
2. Replace any code-like print statements with DESCRIPTIVE MESSAGES:
   - Change print("if x > 5:") to print("Check if value exceeds 5")
   - Change print("x = 10") to print("Set value to 10")
   - Change print("return result") to print("Return final result")
3. Make every print statement human-readable and business-focused
4. Keep all if/else/loop structure
5. Return ONLY the function code

Return the optimized function:""",
            expected_output="A function with descriptive print statements ready for flowchart visualization.",
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

        is_valid, msg = validate_code_structure(cleaned_code)
        if not is_valid:
            logger.warning(f"Cleaned code still invalid: {msg}")
            if "No function definition found" in msg:
                cleaned_code = wrap_code_in_function(cleaned_code)

        return cleaned_code
    except Exception as e:
        logger.error(f"Error cleaning code: {e}\n{traceback.format_exc()}")
        try:
            return wrap_code_in_function(code)
        except:
            return code


def detect_first_function(code: str) -> tuple[str, bool]:
    """Detect first function name and return whether it was found."""
    try:
        match = re.search(r'def\s+(\w+)\s*\(', code)
        if match:
            func_name = match.group(1)
            logger.info(f"✅ Detected function: {func_name}")
            return func_name, True
        else:
            logger.warning("⚠️ No function detected in code!")
            logger.warning(f"Code preview:\n{code[:200]}...")
            return "main", False
    except Exception as e:
        logger.error(f"Error detecting function: {e}")
        return "main", False


def generate_flowchart_html(code: str, field_name: str, html_filename: str):
    logger.info(f"Generating flowchart HTML for function: {field_name}")
    try:
        fc = Flowchart.from_code(code, field=field_name, inner=False)
        flowchart_str = fc.flowchart()

        # Create enhanced HTML with download buttons
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Flowchart - {field_name}</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/raphael/2.3.0/raphael.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/flowchart/1.17.1/flowchart.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
            font-family: Arial, sans-serif;
        }}
        .container {{
            max-width: 100%;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .controls {{
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        button {{
            padding: 10px 20px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
        }}
        button:hover {{
            background: #45a049;
        }}
        .svg-button {{
            background: #2196F3;
        }}
        .svg-button:hover {{
            background: #0b7dda;
        }}
        #diagram {{
            display: inline-block;
            background: white;
            padding: 20px;
        }}
        .title {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="title">Flowchart: {field_name}</div>
        <div class="controls">
            <button onclick="downloadPNG()">📥 Download PNG</button>
            <button class="svg-button" onclick="downloadSVG()">📥 Download SVG</button>
        </div>
        <div id="diagram"></div>
    </div>

    <script>
        var code = `{flowchart_str}`;
        var diagram = flowchart.parse(code);

        // Draw the flowchart
        diagram.drawSVG('diagram', {{
            'x': 0,
            'y': 0,
            'line-width': 2,
            'line-length': 50,
            'text-margin': 10,
            'font-size': 14,
            'font': 'normal',
            'font-family': 'Arial',
            'font-weight': 'normal',
            'font-color': 'black',
            'line-color': 'black',
            'element-color': 'black',
            'fill': 'white',
            'yes-text': 'yes',
            'no-text': 'no',
            'arrow-end': 'block',
            'scale': 1,
            'symbols': {{
                'start': {{
                    'font-color': 'black',
                    'element-color': 'black',
                    'fill': '#90EE90'
                }},
                'end': {{
                    'font-color': 'white',
                    'element-color': 'black',
                    'fill': '#FF6B6B'
                }}
            }},
            'flowstate': {{
                'approved': {{'fill': '#90EE90'}},
                'rejected': {{'fill': '#FFB6C1'}},
                'processing': {{'fill': '#ADD8E6'}}
            }}
        }});

        // Function to download as PNG
        function downloadPNG() {{
            try {{
                var svg = document.querySelector('#diagram svg');
                if (!svg) {{
                    alert('SVG not found!');
                    return;
                }}

                // Get SVG dimensions
                var bbox = svg.getBBox();
                var padding = 40;
                var width = bbox.width + bbox.x + padding * 2;
                var height = bbox.height + bbox.y + padding * 2;

                // Create canvas
                var canvas = document.createElement('canvas');
                canvas.width = width;
                canvas.height = height;
                var ctx = canvas.getContext('2d');

                // Fill white background
                ctx.fillStyle = 'white';
                ctx.fillRect(0, 0, width, height);

                // Get SVG data
                var svgData = new XMLSerializer().serializeToString(svg);

                // Create image from SVG
                var img = new Image();
                var svgBlob = new Blob([svgData], {{type: 'image/svg+xml;charset=utf-8'}});
                var url = URL.createObjectURL(svgBlob);

                img.onload = function() {{
                    // Draw image on canvas with padding
                    ctx.drawImage(img, padding, padding);

                    // Convert to PNG and download
                    canvas.toBlob(function(blob) {{
                        var link = document.createElement('a');
                        link.download = 'flowchart_{field_name}.png';
                        link.href = URL.createObjectURL(blob);
                        link.click();
                        URL.revokeObjectURL(url);
                        URL.revokeObjectURL(link.href);
                    }}, 'image/png');
                }};

                img.onerror = function() {{
                    alert('Error generating PNG. Please try SVG download instead.');
                    URL.revokeObjectURL(url);
                }};

                img.src = url;
            }} catch (error) {{
                console.error('Error downloading PNG:', error);
                alert('Error downloading PNG: ' + error.message);
            }}
        }}

        // Function to download as SVG
        function downloadSVG() {{
            try {{
                var svg = document.querySelector('#diagram svg');
                if (!svg) {{
                    alert('SVG not found!');
                    return;
                }}

                // Clone and prepare SVG for download
                var svgClone = svg.cloneNode(true);

                // Set proper dimensions
                var bbox = svg.getBBox();
                svgClone.setAttribute('width', bbox.width + bbox.x + 40);
                svgClone.setAttribute('height', bbox.height + bbox.y + 40);
                svgClone.setAttribute('viewBox', `${{bbox.x - 20}} ${{bbox.y - 20}} ${{bbox.width + 40}} ${{bbox.height + 40}}`);

                // Get SVG string
                var svgData = new XMLSerializer().serializeToString(svgClone);

                // Add XML declaration
                svgData = '<?xml version="1.0" encoding="UTF-8"?>\\n' + svgData;

                // Create blob and download
                var blob = new Blob([svgData], {{type: 'image/svg+xml;charset=utf-8'}});
                var link = document.createElement('a');
                link.download = 'flowchart_{field_name}.svg';
                link.href = URL.createObjectURL(blob);
                link.click();
                URL.revokeObjectURL(link.href);
            }} catch (error) {{
                console.error('Error downloading SVG:', error);
                alert('Error downloading SVG: ' + error.message);
            }}
        }}

        console.log('Flowchart rendered successfully');
    </script>
</body>
</html>"""

        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"✅ Enhanced HTML with download buttons generated: {html_filename}")
        return html_filename, flowchart_str
    except AssertionError as e:
        logger.error(f"❌ Flowchart generation failed: {e}")
        logger.error(f"Function name: {field_name}")
        logger.error(f"Code being parsed:\n{'-' * 50}\n{code}\n{'-' * 50}")
        raise
    except Exception as e:
        logger.error(f"Error generating flowchart HTML: {e}\n{traceback.format_exc()}")
        raise


def generate_flowchart_from_prompt(user_prompt: str, job_id: str):
    logger.info(f"Generating flowchart HTML for function: {field_name}")
    try:
        fc = Flowchart.from_code(code, field=field_name, inner=False)
        flowchart_str = fc.flowchart()

        # Create enhanced HTML with download buttons
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Flowchart - {field_name}</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/raphael/2.3.0/raphael.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/flowchart/1.17.1/flowchart.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
            font-family: Arial, sans-serif;
        }}
        .container {{
            max-width: 100%;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .controls {{
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        button {{
            padding: 10px 20px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
        }}
        button:hover {{
            background: #45a049;
        }}
        .svg-button {{
            background: #2196F3;
        }}
        .svg-button:hover {{
            background: #0b7dda;
        }}
        #diagram {{
            display: inline-block;
            background: white;
            padding: 20px;
        }}
        .title {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="title">Flowchart: {field_name}</div>
        <div class="controls">
            <button onclick="downloadPNG()">📥 Download PNG</button>
            <button class="svg-button" onclick="downloadSVG()">📥 Download SVG</button>
        </div>
        <div id="diagram"></div>
    </div>

    <script>
        var code = `{flowchart_str}`;
        var diagram = flowchart.parse(code);

        // Draw the flowchart
        diagram.drawSVG('diagram', {{
            'x': 0,
            'y': 0,
            'line-width': 2,
            'line-length': 50,
            'text-margin': 10,
            'font-size': 14,
            'font': 'normal',
            'font-family': 'Arial',
            'font-weight': 'normal',
            'font-color': 'black',
            'line-color': 'black',
            'element-color': 'black',
            'fill': 'white',
            'yes-text': 'yes',
            'no-text': 'no',
            'arrow-end': 'block',
            'scale': 1,
            'symbols': {{
                'start': {{
                    'font-color': 'black',
                    'element-color': 'black',
                    'fill': '#90EE90'
                }},
                'end': {{
                    'font-color': 'white',
                    'element-color': 'black',
                    'fill': '#FF6B6B'
                }}
            }},
            'flowstate': {{
                'approved': {{'fill': '#90EE90'}},
                'rejected': {{'fill': '#FFB6C1'}},
                'processing': {{'fill': '#ADD8E6'}}
            }}
        }});

        // Function to download as PNG
        function downloadPNG() {{
            try {{
                var svg = document.querySelector('#diagram svg');
                if (!svg) {{
                    alert('SVG not found!');
                    return;
                }}

                // Get SVG dimensions
                var bbox = svg.getBBox();
                var padding = 40;
                var width = bbox.width + bbox.x + padding * 2;
                var height = bbox.height + bbox.y + padding * 2;

                // Create canvas
                var canvas = document.createElement('canvas');
                canvas.width = width;
                canvas.height = height;
                var ctx = canvas.getContext('2d');

                // Fill white background
                ctx.fillStyle = 'white';
                ctx.fillRect(0, 0, width, height);

                // Get SVG data
                var svgData = new XMLSerializer().serializeToString(svg);

                // Create image from SVG
                var img = new Image();
                var svgBlob = new Blob([svgData], {{type: 'image/svg+xml;charset=utf-8'}});
                var url = URL.createObjectURL(svgBlob);

                img.onload = function() {{
                    // Draw image on canvas with padding
                    ctx.drawImage(img, padding, padding);

                    // Convert to PNG and download
                    canvas.toBlob(function(blob) {{
                        var link = document.createElement('a');
                        link.download = 'flowchart_{field_name}.png';
                        link.href = URL.createObjectURL(blob);
                        link.click();
                        URL.revokeObjectURL(url);
                        URL.revokeObjectURL(link.href);
                    }}, 'image/png');
                }};

                img.onerror = function() {{
                    alert('Error generating PNG. Please try SVG download instead.');
                    URL.revokeObjectURL(url);
                }};

                img.src = url;
            }} catch (error) {{
                console.error('Error downloading PNG:', error);
                alert('Error downloading PNG: ' + error.message);
            }}
        }}

        // Function to download as SVG
        function downloadSVG() {{
            try {{
                var svg = document.querySelector('#diagram svg');
                if (!svg) {{
                    alert('SVG not found!');
                    return;
                }}

                // Clone and prepare SVG for download
                var svgClone = svg.cloneNode(true);

                // Set proper dimensions
                var bbox = svg.getBBox();
                svgClone.setAttribute('width', bbox.width + bbox.x + 40);
                svgClone.setAttribute('height', bbox.height + bbox.y + 40);
                svgClone.setAttribute('viewBox', `${{bbox.x - 20}} ${{bbox.y - 20}} ${{bbox.width + 40}} ${{bbox.height + 40}}`);

                // Get SVG string
                var svgData = new XMLSerializer().serializeToString(svgClone);

                // Add XML declaration
                svgData = '<?xml version="1.0" encoding="UTF-8"?>\\n' + svgData;

                // Create blob and download
                var blob = new Blob([svgData], {{type: 'image/svg+xml;charset=utf-8'}});
                var link = document.createElement('a');
                link.download = 'flowchart_{field_name}.svg';
                link.href = URL.createObjectURL(blob);
                link.click();
                URL.revokeObjectURL(link.href);
            }} catch (error) {{
                console.error('Error downloading SVG:', error);
                alert('Error downloading SVG: ' + error.message);
            }}
        }}

        console.log('Flowchart rendered successfully');
    </script>
</body>
</html>"""

        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"✅ Enhanced HTML with download buttons generated: {html_filename}")
        return html_filename, flowchart_str
    except AssertionError as e:
        logger.error(f"❌ Flowchart generation failed: {e}")
        logger.error(f"Function name: {field_name}")
        logger.error(f"Code being parsed:\n{'-' * 50}\n{code}\n{'-' * 50}")
        raise
    except Exception as e:
        logger.error(f"Error generating flowchart HTML: {e}\n{traceback.format_exc()}")
        raise


def render_and_download_selenium(html_file: str, svg_content: str, png_file: str, svg_file: str):
    """Use Selenium to render HTML to PNG with better handling."""
    logger.info("Starting render with Selenium...")
    driver = None
    try:
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")

        # Initialize Chrome driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Load HTML
        abs_path = f"file:///{os.path.abspath(html_file).replace(os.sep, '/')}"
        logger.info(f"Loading HTML from: {abs_path}")
        driver.get(abs_path)

        # Wait longer for flowchart.js to render
        time.sleep(5)

        # Check if SVG was rendered
        svg_elements = driver.find_elements("tag name", "svg")
        logger.info(f"Found {len(svg_elements)} SVG elements")

        if len(svg_elements) == 0:
            logger.error("No SVG elements found! Flowchart may not have rendered.")
            # Save page source for debugging
            with open(html_file.replace('.html', '_debug.html'), 'w') as f:
                f.write(driver.page_source)
            raise Exception("No SVG elements found in rendered HTML")

        svg_element = svg_elements[0]

        # Get actual SVG dimensions using JavaScript
        try:
            svg_width = driver.execute_script("""
                var svg = arguments[0];
                var bbox = svg.getBBox();
                return bbox.width + bbox.x;
            """, svg_element)

            svg_height = driver.execute_script("""
                var svg = arguments[0];
                var bbox = svg.getBBox();
                return bbox.height + bbox.y;
            """, svg_element)

            logger.info(f"SVG content dimensions: {svg_width}x{svg_height}")

            # Add padding and set window size
            padding = 50
            window_width = max(int(svg_width + padding * 2), 800)
            window_height = max(int(svg_height + padding * 2), 600)

            logger.info(f"Setting window size to: {window_width}x{window_height}")
            driver.set_window_size(window_width, window_height)
            time.sleep(2)

        except Exception as e:
            logger.warning(f"Could not get SVG dimensions: {e}")
            # Use default large size
            driver.set_window_size(2000, 2000)
            time.sleep(2)

        # Scroll to element to ensure it's in viewport
        driver.execute_script("arguments[0].scrollIntoView(true);", svg_element)
        time.sleep(1)

        # Take screenshot of SVG element
        svg_element.screenshot(png_file)
        logger.info(f"✅ PNG saved: {png_file}")

        # Get SVG HTML and save
        svg_html = driver.execute_script("return arguments[0].outerHTML;", svg_element)

        # Fix SVG dimensions in saved file
        svg_html = fix_svg_dimensions(svg_html)

        with open(svg_file, 'w', encoding='utf-8') as f:
            f.write(svg_html)
        logger.info(f"✅ SVG saved: {svg_file}")

    except Exception as e:
        logger.error(f"Error in render_and_download_selenium: {e}\n{traceback.format_exc()}")

        # Try fallback: full page screenshot
        try:
            if driver:
                driver.save_screenshot(png_file)
                logger.info(f"✅ Fallback PNG saved: {png_file}")

                # Save original SVG content
                with open(svg_file, 'w', encoding='utf-8') as f:
                    f.write(svg_content if svg_content else "<svg></svg>")
                logger.info(f"✅ Fallback SVG saved: {svg_file}")
        except Exception as fallback_error:
            logger.error(f"Fallback also failed: {fallback_error}")
            raise e
    finally:
        if driver:
            driver.quit()


def generate_flowchart_from_prompt(user_prompt: str, job_id: str):
    logger.info(f"🚀 Starting flowchart generation for job: {job_id}")
    try:
        # Generate filenames
        html_file = OUTPUT_DIR / f"{job_id}.html"

        # Step 1: Generate code
        logger.info("Step 1: Generating Python code...")
        python_code = generate_python_code(user_prompt)

        # Step 2: Clean/fix code
        logger.info("Step 2: Cleaning/fixing Python code...")
        cleaned_code = clean_python_code(python_code)

        # Step 3: Validate cleaned code
        is_valid, msg = validate_code_structure(cleaned_code)
        if not is_valid:
            error_msg = f"Code validation failed after cleaning: {msg}\n\nCode:\n{cleaned_code}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Step 4: Detect function
        logger.info("Step 3: Detecting function name...")
        function_name, found = detect_first_function(cleaned_code)

        if not found:
            error_msg = f"No function definition found in cleaned code!\n\nCode:\n{cleaned_code}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"✅ Using function: {function_name}")

        # Step 5: Generate HTML with download buttons
        logger.info("Step 4: Generating interactive flowchart HTML...")
        html_file_path, svg_content = generate_flowchart_html(cleaned_code, function_name, str(html_file))

        logger.info(f"✅ Flowchart generation completed for job: {job_id}")
        logger.info(f"   View at: /view/{job_id}")
        return cleaned_code
    except Exception as e:
        logger.error(f"❌ Error in generate_flowchart_from_prompt: {e}\n{traceback.format_exc()}")
        raise


@app.get("/")
async def root():
    return {
        "message": "Flowchart Generator API",
        "version": "2.1.0",
        "status": "operational" if llm else "llm_not_initialized",
        "description": "Generate flowcharts with browser-based PNG/SVG download",
        "endpoints": {
            "POST /generate": "Generate flowchart from prompt",
            "GET /view/{job_id}": "View interactive flowchart with download buttons",
            "GET /download/svg/{job_id}": "Download SVG file",
            "GET /download/png/{job_id}": "Download PNG file (if generated)",
            "GET /health": "Check API health",
            "DELETE /cleanup/{job_id}": "Delete generated files"
        },
        "usage": "1. POST to /generate with prompt, 2. Open /view/{job_id} in browser, 3. Click 'Download PNG' button for complete image"
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
    logger.info(f"📨 Received generate request: {request.prompt}")

    if not llm:
        raise HTTPException(status_code=500, detail="LLM not initialized. Check MISTRAL_KEY environment variable.")

    if not request.prompt or len(request.prompt.strip()) == 0:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        logger.info(f"🆔 Generated job_id: {job_id}")

        # Generate flowchart
        generated_code = generate_flowchart_from_prompt(request.prompt, job_id)

        return FlowchartResponse(
            job_id=job_id,
            message="Flowchart generated successfully. Open view_url in browser to download PNG/SVG.",
            view_url=f"/view/{job_id}",
            svg_url=f"/download/svg/{job_id}",
            png_url=f"/download/png/{job_id}",
            generated_code=generated_code
        )
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=422,
            detail={
                "error": "Code validation failed",
                "message": str(e),
                "hint": "The LLM failed to generate valid Python code with a function definition. Try rephrasing your prompt."
            }
        )
    except Exception as e:
        logger.error(f"❌ Error in generate_flowchart endpoint: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "type": type(e).__name__,
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


@app.get("/view/{job_id}")
async def view_flowchart(job_id: str):
    """View the interactive flowchart HTML with download buttons"""
    html_file = OUTPUT_DIR / f"{job_id}.html"

    if not html_file.exists():
        logger.error(f"HTML file not found: {html_file}")
        raise HTTPException(status_code=404, detail="Flowchart not found")

    return FileResponse(
        path=html_file,
        media_type="text/html",
        filename=f"flowchart_{job_id}.html"
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
            logger.info(f"🗑️ Deleted: {file_path}")

    return {"message": "Files cleaned up", "deleted_files": deleted}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 9000))
    logger.info(f"🚀 Starting server on port {port}")
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=True)