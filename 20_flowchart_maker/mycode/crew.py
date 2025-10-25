"""
CrewAI Flowchart Generator - Fully Automated with PNG Export
User provides a query, system generates code and flowchart PNG automatically
"""

from crewai import Agent, Task, Crew, Process
import os
from pyflowchart import Flowchart
import re
from graphviz import Digraph
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image, ImageDraw, ImageFont
import io

# Initialize LLM
from llm import gemini_llm

# Define Agents
requirements_analyzer = Agent(
    role='Requirements Analyzer',
    goal='Understand user requirements and create a detailed specification for code generation',
    backstory="""You are an expert business analyst who can understand user requirements 
    and translate them into clear, detailed specifications. You excel at identifying the 
    core logic, inputs, outputs, and decision points needed.""",
    verbose=True,
    allow_delegation=False,
    llm=gemini_llm
)

code_generator = Agent(
    role='Code Generator',
    goal='Generate clean, functional Python code based on specifications',
    backstory="""You are a senior Python developer who writes clean, well-structured code. 
    You create simple, readable functions with clear logic flow, proper conditionals, 
    and loops. Your code is perfect for flowchart generation.""",
    verbose=True,
    allow_delegation=False,
    llm=gemini_llm
)

flowchart_specialist = Agent(
    role='Flowchart Specialist',
    goal='Validate and optimize code for flowchart generation',
    backstory="""You are a flowchart expert who ensures code is optimized for 
    pyflowchart conversion. You verify the code structure, add necessary comments, 
    and ensure the logic flow is clear and visualizable.""",
    verbose=True,
    allow_delegation=False,
    llm=gemini_llm
)


def create_automated_flowchart_crew(user_query: str):
    """
    Create a crew that automatically generates code and flowchart from user query
    """

    # Task 1: Analyze requirements
    requirements_task = Task(
        description=f"""Analyze this user request and create a detailed specification:
        
        USER REQUEST: {user_query}
        
        Create a specification that includes:
        1. What the program should do
        2. Required inputs
        3. Processing logic and decision points
        4. Expected outputs
        5. Any loops or iterations needed
        
        Be specific and detailed.""",
        agent=requirements_analyzer,
        expected_output="Detailed specification with inputs, logic flow, and outputs"
    )

    # Task 2: Generate Python code
    code_task = Task(
        description="""Based on the specification, generate clean Python code.
        
        REQUIREMENTS:
        - Create a complete, working Python program
        - Use clear function names and variable names
        - Include if/else statements for decisions
        - Use loops (for/while) where needed
        - Add input() for user inputs if needed
        - Add print() for outputs
        - Keep it simple and clear
        
        CRITICAL: Output ONLY the Python code in a code block, nothing else.
        Format: ```python\n[code here]\n```""",
        agent=code_generator,
        expected_output="Complete Python code in a code block",
        context=[requirements_task]
    )

    # Task 3: Validate and optimize for flowchart
    validation_task = Task(
        description="""Review the generated code and optimize it for flowchart generation.
        
        Check:
        - Code structure is clear
        - Logic flow is easy to follow
        - All paths are properly defined
        - Comments explain the flow
        
        Output the final, optimized Python code ONLY in a code block.
        Format: ```python\n[code here]\n```""",
        agent=flowchart_specialist,
        expected_output="Validated Python code in a code block",
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
    """
    Extract Python code from crew output
    """
    # Try to find code in markdown code blocks
    pattern = r'```python\s*(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)

    if matches:
        return matches[-1].strip()

    # If no code block found, try to extract any Python-looking code
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
    """
    Parse flowchart definition into nodes and connections
    """
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

                # Parse node type and text
                if ':' in node_def:
                    node_type, node_text = node_def.split(':', 1)
                    node_type = node_type.strip()
                    node_text = node_text.strip()
                    nodes[node_id] = {'type': node_type, 'text': node_text}

        # Parse connections
        elif '->' in line:
            # Handle conditional connections
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
    """
    Create a PNG image of the flowchart using Graphviz
    """
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

        # Customize based on node type
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
    Fully automated function: Takes user query, generates code, creates flowchart PNG and HTML
    """
    print("🚀 Starting Automated Flowchart Generator...")
    print("=" * 70)
    print(f"📝 User Query: {user_query}")
    print("=" * 70)

    try:
        # Step 1: Generate code from query using CrewAI
        print("\n🤖 Step 1: Analyzing requirements and generating code...")
        crew = create_automated_flowchart_crew(user_query)
        result = crew.kickoff()

        # Extract the generated code
        generated_code = extract_python_code(str(result))
        print("\n✅ Code generation complete!")
        print("\n📄 Generated Code:")
        print("-" * 70)
        print(generated_code)
        print("-" * 70)

        # Step 2: Generate flowchart using pyflowchart
        print("\n📊 Step 2: Generating flowchart definition...")
        fc = Flowchart.from_code(generated_code)
        flowchart_code = fc.flowchart()
        print("✅ Flowchart definition generated!")

        # Step 3: Create PNG image
        print("\n🎨 Step 3: Creating PNG image...")
        png_file = output_file.replace('.html', '.png')
        png_created = create_flowchart_png(flowchart_code, png_file)

        # Step 4: Create HTML with embedded PNG
        print("\n📄 Step 4: Creating HTML visualization...")

        # Create relative path for the image
        png_filename = os.path.basename(png_file)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flowchart - {user_query[:50]}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
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
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .content {{
            padding: 40px;
        }}
        .query-box {{
            background: #f0f4ff;
            border-left: 5px solid #667eea;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .query-box h3 {{
            color: #667eea;
            margin-bottom: 10px;
        }}
        .query-box p {{
            color: #333;
            line-height: 1.6;
        }}
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
        .download-btn {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 12px 30px;
            border-radius: 25px;
            text-decoration: none;
            margin: 20px 10px;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(102,126,234,0.3);
        }}
        .download-btn:hover {{
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102,126,234,0.4);
        }}
        .code-section {{
            margin-top: 40px;
        }}
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
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }}
        .code-box pre {{
            margin: 0;
            white-space: pre;
        }}
        .flowchart-def {{
            background: #f5f5f5;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
            overflow-x: auto;
        }}
        .flowchart-def pre {{
            margin: 0;
            color: #333;
            font-family: monospace;
            white-space: pre-wrap;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e0e0e0;
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
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .info-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}
        .info-card h4 {{
            margin-bottom: 10px;
            font-size: 1.2em;
        }}
        .info-card p {{
            opacity: 0.9;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔄 Automated Flowchart Generator</h1>
            <p>Powered by CrewAI & PyFlowchart</p>
            <span class="badge">✨ Auto-Generated PNG</span>
        </div>
        
        <div class="content">
            <div class="query-box">
                <h3>📝 Your Request:</h3>
                <p>{user_query}</p>
            </div>
            
            <h2 style="text-align: center; color: #333; margin: 30px 0;">📊 Visual Flowchart</h2>
            
            <div class="flowchart-container">
                {"<img src='" + png_filename + "' alt='Flowchart' />" if png_created else "<p style='color: #dc3545; padding: 40px;'>⚠️ PNG generation failed. Please check Graphviz installation.</p>"}
                
                {f'''<div style="margin-top: 20px;">
                    <a href="{png_filename}" download class="download-btn">⬇️ Download PNG</a>
                </div>''' if png_created else ''}
            </div>
            
            <div class="info-grid">
                <div class="info-card">
                    <h4>🤖 AI-Powered</h4>
                    <p>Code generated by CrewAI agents</p>
                </div>
                <div class="info-card">
                    <h4>🎨 Visual Output</h4>
                    <p>PNG image with nodes & connections</p>
                </div>
                <div class="info-card">
                    <h4>⚡ Fully Automated</h4>
                    <p>From query to flowchart in seconds</p>
                </div>
            </div>
            
            <div class="code-section">
                <h3>💻 Generated Python Code</h3>
                <div class="code-box">
                    <pre>{generated_code}</pre>
                </div>
            </div>
            
            <div class="code-section">
                <h3>🔤 Flowchart Definition</h3>
                <div class="flowchart-def">
                    <pre>{flowchart_code}</pre>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated automatically using CrewAI agents 🤖</p>
            <p style="margin-top: 10px; font-size: 0.9em;">
                Code Analysis → Generation → Validation → Flowchart PNG Creation
            </p>
        </div>
    </div>
</body>
</html>"""

        # Save HTML file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✅ HTML created successfully!")
        print("\n" + "=" * 70)
        print(f"🎉 COMPLETE!")
        print(f"📄 HTML: {output_file}")
        if png_created:
            print(f"🖼️  PNG:  {png_file}")
        print(f"🌐 Open '{output_file}' in your browser to view the result")
        print("=" * 70)

        return output_file

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Troubleshooting tips:")
        print("   - Make sure your query is clear and specific")
        print("   - Check that the LLM is properly configured")
        print("   - Verify dependencies: pip install pyflowchart graphviz")
        print("   - Install Graphviz system package: apt-get install graphviz (Linux) or brew install graphviz (Mac)")
        return None


# Example usage
if __name__ == "__main__":
    # User just provides their query - everything else is automated!

    # Example 1: Simple calculator
    query1 = "Create a program that checks if a number is positive, negative, or zero"

    # Example 2: More complex
    query2 = "Build a simple ATM system that checks PIN, shows balance, and allows withdrawal"

    # Example 3: Grade calculator
    query3 = "Make a student grade calculator that converts scores to letter grades"

    # Run the generator
    print("🎯 Choose an example or provide your own query:\n")
    print("1. Number checker (positive/negative/zero)")
    print("2. ATM system")
    print("3. Grade calculator")
    print("\nUsing Example 3...\n")

    generate_flowchart_from_query(query3, "automated_flowchart.html")

    print("\n" + "=" * 70)
    print("🚀 Want to try another query? Just call:")
    print("   generate_flowchart_from_query('your query here', 'output.html')")
    print("=" * 70)