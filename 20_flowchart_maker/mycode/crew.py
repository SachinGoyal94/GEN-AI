"""
CrewAI Flowchart Generator - Conceptual Flow (No Execution)
Generates Python code for flowchart visualization only - HTML output via pyflowchart
"""

from crewai import Agent, Task, Crew, Process
import re
from pyflowchart import Flowchart, output_html

# Initialize LLM
from llm import gemini_llm

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
    """
    Create a crew that generates conceptual Python code for flowchart visualization
    """

    # Task 1: Analyze requirements
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

    # Task 2: Generate conceptual Python code
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

    # Task 3: Optimize for flowchart
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

    # Create and run the crew
    crew = Crew(
        agents=[requirements_analyzer, code_generator, flowchart_specialist],
        tasks=[requirements_task, code_task, validation_task],
        process=Process.sequential,
        verbose=True
    )

    return crew


def extract_python_code(text: str) -> str:
    """Extract Python code from crew output"""
    # Find code in markdown code blocks
    pattern = r'```python\s*(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)

    if matches:
        return matches[-1].strip()

    # Fallback: extract Python-like code
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


def generate_flowchart_from_query(user_query: str, output_file: str = "flowchart.html"):
    """
    Generate conceptual code and flowchart HTML from user query
    """
    print("🚀 Starting Flowchart Generator (Conceptual Flow)...")
    print("=" * 70)
    print(f"📝 User Query: {user_query}")
    print("=" * 70)

    try:
        # Step 1: Generate conceptual code
        print("\n🤖 Step 1: Analyzing requirements and generating conceptual code...")
        crew = create_flowchart_crew(user_query)
        result = crew.kickoff()

        # Extract the generated code
        generated_code = extract_python_code(str(result))
        print("\n✅ Conceptual code generation complete!")
        print("\n📄 Generated Code (For Flowchart Visualization):")
        print("-" * 70)
        print(generated_code)
        print("-" * 70)

        # Step 2: Generate flowchart
        print("\n📊 Step 2: Generating flowchart definition...")
        fc = Flowchart.from_code(generated_code)
        flowchart_code = fc.flowchart()
        print("\n✅ Flowchart definition generated!")
        print("-" * 70)
        print(flowchart_code)
        print("-" * 70)

        # Step 3: Generate HTML using pyflowchart's built-in function
        print("\n🎨 Step 3: Creating HTML flowchart...")
        output_html(
            output_name=output_file,
            field_name="flowchart_visualization",
            flowchart=flowchart_code
        )
        print(f"✅ HTML flowchart created: {output_file}")

        print("\n" + "=" * 70)
        print(f"🎉 COMPLETE!")
        print(f"📄 HTML: {output_file}")
        print(f"🌐 Open '{output_file}' in your browser to view the flowchart")
        print("=" * 70)

        return {
            'html_file': output_file,
            'generated_code': generated_code,
            'flowchart_definition': flowchart_code
        }

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    query = "if a user is of age 18 they are eligible to drive both lmv and hmv type vehicles if they apply for driving license they need  to clear a driving test if cleared then after each 1 year they have to renew it till the age of 70 when the license will be limited to lmv type vehicles only"

    # Generate flowchart HTML
    result = generate_flowchart_from_query(query, "driving_license_flowchart.html")

    if result:
        print("\n✅ Success! You now have:")
        print(f"   📄 Flowchart HTML: {result['html_file']}")
        print(f"   💻 Generated Code: Available in result['generated_code']")
        print(f"   🔤 Flowchart Definition: Available in result['flowchart_definition']")