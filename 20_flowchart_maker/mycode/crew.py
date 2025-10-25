"""
CrewAI Flowchart Generator - Conceptual Flow (No Execution)
Generates Python code for flowchart visualization only
"""

from crewai import Agent, Task, Crew, Process
import os
from pyflowchart import Flowchart
import re
from graphviz import Digraph

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


def parse_flowchart_definition(flowchart_def: str):
    """Parse flowchart definition into nodes and connections"""
    nodes = {}
    connections = []

    lines = flowchart_def.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Parse node definitions
        if '=>' in line and '->' not in line:
            parts = line.split('=>')
            if len(parts) == 2:
                node_id = parts[0].strip()
                node_def = parts[1].strip()

                if ':' in node_def:
                    node_type, node_text = node_def.split(':', 1)
                    node_type = node_type.strip()
                    node_text = node_text.strip()
                    nodes[node_id] = {'type': node_type, 'text': node_text}

        # Parse connections
        elif '->' in line:
            if '(yes)' in line or '(no)' in line:
                parts = line.split('->')
                source = parts[0].strip()
                if '(yes)' in source:
                    source_id = source.replace('(yes)', '').strip()
                    label = 'Yes'
                elif '(no)' in source:
                    source_id = source.replace('(no)', '').strip()
                    label = 'No'
                else:
                    source_id = source
                    label = None

                target = parts[1].strip() if len(parts) > 1 else None
                if target:
                    connections.append({'from': source_id, 'to': target, 'label': label})
            else:
                parts = line.split('->')
                if len(parts) >= 2:
                    source = parts[0].strip()
                    target = parts[1].strip()
                    connections.append({'from': source, 'to': target, 'label': None})

    return nodes, connections


def create_flowchart_png(flowchart_def: str, output_file: str):
    """Create a PNG image of the flowchart using Graphviz"""
    nodes, connections = parse_flowchart_definition(flowchart_def)

    # Create a Graphviz Digraph
    dot = Digraph(comment='Flowchart', format='png')
    dot.attr(rankdir='TB', size='12,16')
    dot.attr('node', shape='box', style='rounded,filled', fillcolor='lightblue',
             fontname='Arial', fontsize='12', margin='0.2,0.1')
    dot.attr('edge', fontname='Arial', fontsize='10')

    # Add nodes with appropriate shapes
    for node_id, node_info in nodes.items():
        node_type = node_info['type']
        node_text = node_info['text']

        if node_type == 'start' or node_type == 'end':
            dot.node(node_id, node_text, shape='ellipse',
                    fillcolor='#90EE90' if node_type == 'start' else '#FFB6C6',
                    style='filled', fontcolor='white', fontsize='14', penwidth='2')
        elif node_type == 'condition':
            dot.node(node_id, node_text, shape='diamond',
                    fillcolor='#FFE4B5', style='filled', fontsize='11')
        elif node_type == 'inputoutput':
            dot.node(node_id, node_text, shape='parallelogram',
                    fillcolor='#B0E0E6', style='filled')
        elif node_type == 'operation':
            dot.node(node_id, node_text, shape='box',
                    fillcolor='#E6E6FA', style='rounded,filled')
        else:
            dot.node(node_id, node_text, fillcolor='lightgray')

    # Add connections
    for conn in connections:
        if conn['label']:
            dot.edge(conn['from'], conn['to'], label=conn['label'],
                    color='#666666', penwidth='2')
        else:
            dot.edge(conn['from'], conn['to'], color='#666666', penwidth='2')

    # Render to PNG
    try:
        dot.render(output_file.replace('.png', ''), cleanup=True)
        print(f"✅ Flowchart PNG created: {output_file}")
        return True
    except Exception as e:
        print(f"❌ Error creating PNG with Graphviz: {e}")
        print("💡 Make sure Graphviz is installed: apt-get install graphviz or brew install graphviz")
        return False


def generate_flowchart_from_query(user_query: str, output_file: str = "flowchart.html"):
    """
    Generate conceptual code and flowchart from user query
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
        print("✅ Flowchart definition generated!")

        # Step 3: Create PNG
        print("\n🎨 Step 3: Creating PNG image...")
        png_file = output_file.replace('.html', '.png')
        png_created = create_flowchart_png(flowchart_code, png_file)

        # Step 4: Create HTML
        print("\n📄 Step 4: Creating HTML visualization...")
        png_filename = os.path.basename(png_file)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flowchart - {user_query[:50]}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        .badge {{
            display: inline-block;
            background: #28a745;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            margin: 10px 0;
        }}
        .content {{ padding: 40px; }}
        .query-box {{
            background: #f0f4ff;
            border-left: 5px solid #667eea;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .query-box h3 {{ color: #667eea; margin-bottom: 10px; }}
        .flowchart-container {{
            background: #fafafa;
            border-radius: 15px;
            padding: 40px;
            margin: 30px 0;
            text-align: center;
            box-shadow: inset 0 2px 10px rgba(0,0,0,0.05);
        }}
        .flowchart-container img {{
            max-width: 100%;
            height: auto;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .note {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 10px;
            padding: 15px;
            margin: 20px 0;
            color: #856404;
        }}
        .note strong {{ color: #856404; }}
        .code-section {{ margin-top: 40px; }}
        .code-section h3 {{
            color: #333;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        .code-box {{
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 25px;
            border-radius: 10px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.6;
        }}
        .download-btn {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 12px 30px;
            border-radius: 25px;
            text-decoration: none;
            margin: 20px 10px;
            transition: all 0.3s;
        }}
        .download-btn:hover {{
            background: #5568d3;
            transform: translateY(-2px);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔄 Flowchart Generator</h1>
            <p>Conceptual Flow Visualization</p>
            <span class="badge">✨ Logic Flow Only (No Execution)</span>
        </div>
        
        <div class="content">
            <div class="query-box">
                <h3>📝 Your Request:</h3>
                <p>{user_query}</p>
            </div>
            
            <div class="note">
                <strong>📌 Note:</strong> The generated code represents the logic flow for visualization only. 
                It is not meant to be executed. All inputs/outputs are conceptual.
            </div>
            
            <h2 style="text-align: center; color: #333; margin: 30px 0;">📊 Visual Flowchart</h2>
            
            <div class="flowchart-container">
                {"<img src='" + png_filename + "' alt='Flowchart' />" if png_created else "<p style='color: #dc3545;'>⚠️ PNG generation failed</p>"}
                {f'<div><a href="{png_filename}" download class="download-btn">⬇️ Download PNG</a></div>' if png_created else ''}
            </div>
            
            <div class="code-section">
                <h3>💻 Generated Conceptual Code (For Flowchart Only)</h3>
                <div class="code-box"><pre>{generated_code}</pre></div>
            </div>
            
            <div class="code-section">
                <h3>🔤 Flowchart Definition</h3>
                <div class="code-box"><pre>{flowchart_code}</pre></div>
            </div>
        </div>
    </div>
</body>
</html>"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✅ HTML created successfully!")
        print("\n" + "=" * 70)
        print(f"🎉 COMPLETE!")
        print(f"📄 HTML: {output_file}")
        if png_created:
            print(f"🖼️  PNG:  {png_file}")
        print("=" * 70)

        return output_file

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    query = "if a user age is more than 18 they can drive lmv and if more than 24 than hmv incase they are of age 30 and have a license they need to reappear for test and at the age of 60 the license will be valid after regular tests of 6 months each"

    generate_flowchart_from_query(query, "conceptual_flowchart.html")