import os
import asyncio
import re
from pyflowchart import Flowchart, output_html
from pyppeteer import launch
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, LLM

# Load API key
load_dotenv()
mistral_key = os.getenv("MISTRAL_KEY")

# Initialize LLM
llm = LLM(
    model="mistral/mistral-large-latest",
    api_key=mistral_key
)

# CrewAI agent to generate Python code
code_generator = Agent(
    role="Python Flowchart Code Generator",
    goal="Generate Python code for a flowchart based on user requests.",
    backstory="An expert programmer who writes concise Python functions/classes suitable for flowchart visualization.",
    llm=llm
)

# CrewAI agent to clean/fix Python code
code_cleaner = Agent(
    role="Python Code Cleaner",
    goal="Analyze Python code, remove or fix parts that can cause runtime or syntax errors, and return safe code for flowchart generation.",
    backstory="An expert Python developer who ensures that any generated code is syntactically correct and safe to execute for visualization.",
    llm=llm
)

# Python template
python_base = "print('start') <python code> print('end')"


def remove_code_formatting(code: str) -> str:
    """Remove markdown code blocks and triple quotes from generated code."""
    # Remove ```python or ``` markdown blocks
    if "```python" in code:
        code = code.split("```python")[1].split("```")[0].strip()
    elif "```" in code:
        code = code.split("```")[1].split("```")[0].strip()

    # Remove triple quotes at start/end
    code = code.strip()
    if code.startswith('"""') or code.startswith("'''"):
        code = code[3:]
    if code.endswith('"""') or code.endswith("'''"):
        code = code[:-3]

    return code.strip()


# Generate Python code from user prompt
def generate_python_code(user_prompt: str):
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
    print("🧠 Generating Python code...")
    result = crew.kickoff()
    code = result.raw.strip()

    # Clean up formatting
    code = remove_code_formatting(code)

    print("\n✅ Generated Python Code:\n")
    print(code)
    return code


# Clean/fix generated code
def clean_python_code(code: str):
    # Remove any formatting that might have slipped through
    code = remove_code_formatting(code)

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
    print("🧹 Cleaning Python code...")
    result = crew.kickoff()
    cleaned_code = result.raw.strip()

    # Clean up formatting again
    cleaned_code = remove_code_formatting(cleaned_code)

    print("\n✅ Cleaned Python Code:\n")
    print(cleaned_code)
    return cleaned_code


# Automatically detect the first function name
def detect_first_function(code: str):
    match = re.search(r'def (\w+)\s*\(', code)
    if match:
        return match.group(1)
    else:
        return "main"  # fallback if no function found


# Generate flowchart HTML
def generate_flowchart_html(code: str, field_name: str, html_filename="flowchart.html"):
    fc = Flowchart.from_code(code, field=field_name, inner=False)
    flowchart_str = fc.flowchart()
    output_html(html_filename, field_name, flowchart_str)
    return html_filename


# Render HTML to PNG
async def render_html_to_png(html_file: str, png_file: str):
    browser = await launch()
    page = await browser.newPage()
    abs_path = f"file:///{os.path.abspath(html_file)}"
    await page.goto(abs_path, {'waitUntil': 'networkidle0'})
    await page.screenshot({'path': png_file})
    await browser.close()
    print(f"✅ Flowchart saved as {png_file}")


# Main function
def generate_flowchart_from_prompt(user_prompt: str, html_file="flowchart.html", png_file="flowchart.png"):
    # Step 1: Generate code
    python_code = generate_python_code(user_prompt)

    # Step 2: Clean/fix code
    cleaned_code = clean_python_code(python_code)

    # Step 3: Detect function
    function_name = detect_first_function(cleaned_code)
    print(f"\n🔹 Detected function for flowchart: {function_name}")

    # Step 4: Generate HTML + PNG
    html_file = generate_flowchart_html(cleaned_code, function_name, html_file)
    asyncio.run(render_html_to_png(html_file, png_file))


# Example usage
if __name__ == "__main__":
    print("🤖 CrewAI Flowchart Generator (Fully Automatic with Code Cleaning)")
    user_prompt = input("Enter your flowchart request in plain English:\n")
    generate_flowchart_from_prompt(user_prompt)
    print("🎉 Done! Check the PNG file for the flowchart.")