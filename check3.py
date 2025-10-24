import os
import re
import requests
from typing import Type
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, LLM
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

load_dotenv()
gemini_key = os.getenv("GEMINI_KEY")
if not gemini_key:
    raise ValueError("❌ GEMINI_KEY missing in .env file")

llm = LLM(
    model="gemini/gemini-2.5-flash-lite-preview-06-17",
    api_key=gemini_key
)

# Official PlantUML Documentation Links
PLANTUML_DOCS = {
    "use case": "https://plantuml.com/use-case-diagram",
    "activity": "https://plantuml.com/activity-diagram-beta",
    "class": "https://plantuml.com/class-diagram",
    "sequence": "https://plantuml.com/sequence-diagram",
    "component": "https://plantuml.com/component-diagram",
    "state": "https://plantuml.com/state-diagram",
    "object": "https://plantuml.com/object-diagram",
    "deployment": "https://plantuml.com/deployment-diagram",
    "timing": "https://plantuml.com/timing-diagram",
    "network": "https://plantuml.com/nwdiag",
    "wireframe": "https://plantuml.com/salt",
    "archimate": "https://plantuml.com/archimate-diagram",
    "gantt": "https://plantuml.com/gantt-diagram",
    "mindmap": "https://plantuml.com/mindmap-diagram",
    "wbs": "https://plantuml.com/wbs-diagram",
}

# UML Templates for fallback
UML_TEMPLATES = {
    "use case": """@startuml
left to right direction
actor User
actor Admin

rectangle "System" {
    User -- (Login/Register)
    User -- (Use Features)
    Admin -- (Verify Users)
    Admin -- (Manage System)
    (Verify Users) ..> (Login/Register) : includes
}
@enduml""",

    "activity": """@startuml
|User|
start
:Login/Register;
if (Role?) then (Admin)
    |Admin|
    :Manage Users;
    :Deploy Models;
else (User)
    |User|
    :Chat with AI;
    :Use Features;
endif
stop
@enduml""",

    "class": """@startuml
class User {
    +id: int
    +name: string
    +login()
}
class Admin {
    +manageUsers()
}
Admin --|> User
@enduml""",

    "sequence": """@startuml
User -> System: Login Request
System -> Database: Validate
Database --> System: Success
System --> User: Access Granted
@enduml"""
}


# ============================================
# CUSTOM TOOLS USING BaseTool
# ============================================

class FetchDocsInput(BaseModel):
    """Input schema for FetchPlantUMLDocsTool"""
    diagram_type: str = Field(
        ...,
        description="Type of PlantUML diagram (e.g., 'activity', 'use case', 'sequence', 'class')"
    )


class FetchPlantUMLDocsTool(BaseTool):
    name: str = "Fetch PlantUML Documentation"
    description: str = (
        "Fetches official PlantUML documentation for a specific diagram type. "
        "Provide the diagram type (e.g., 'activity', 'use case', 'sequence') "
        "and it will return syntax examples from the official PlantUML website."
    )
    args_schema: Type[BaseModel] = FetchDocsInput

    def _run(self, diagram_type: str) -> str:
        """Fetch documentation from PlantUML official site"""
        diagram_type = diagram_type.lower().strip()

        # Find matching documentation link
        doc_url = None
        for key, url in PLANTUML_DOCS.items():
            if key in diagram_type or diagram_type in key:
                doc_url = url
                break

        if not doc_url:
            available = ", ".join(PLANTUML_DOCS.keys())
            return f"⚠️ No documentation found for '{diagram_type}'.\n\nAvailable types: {available}"

        try:
            print(f"📖 Fetching documentation from: {doc_url}")
            response = requests.get(doc_url, timeout=15)

            if response.status_code == 200:
                content = response.text

                # Extract code examples from HTML
                examples = re.findall(r'<pre[^>]*>(.*?)</pre>', content, re.DOTALL)

                if examples:
                    syntax_guide = f"📚 Official PlantUML Syntax for {diagram_type.upper()}\n"
                    syntax_guide += f"Documentation URL: {doc_url}\n"
                    syntax_guide += "=" * 60 + "\n\n"
                    syntax_guide += "KEY SYNTAX EXAMPLES:\n\n"

                    # Get first few examples
                    for i, example in enumerate(examples[:5], 1):
                        # Clean HTML tags
                        clean_example = re.sub('<[^<]+?>', '', example).strip()
                        if clean_example and len(clean_example) > 10 and "@startuml" in clean_example:
                            syntax_guide += f"Example {i}:\n{'-' * 40}\n{clean_example}\n\n"

                    return syntax_guide
                else:
                    return f"✅ Documentation URL: {doc_url}\n\n(Please refer to the official documentation for complete syntax details)"
            else:
                return f"❌ Failed to fetch documentation. HTTP Status: {response.status_code}\nURL: {doc_url}"

        except Exception as e:
            return f"❌ Error fetching documentation: {str(e)}\nAttempted URL: {doc_url}"


class GetAvailableDocsInput(BaseModel):
    """Input schema for GetAvailableDocsTool"""
    query: str = Field(
        default="all",
        description="Query parameter (use 'all' to get all available docs)"
    )


class GetAvailableDocsTool(BaseTool):
    name: str = "Get Available Documentation Links"
    description: str = (
        "Returns all available PlantUML diagram types and their official documentation URLs. "
        "Use this to see what diagram types are supported."
    )
    args_schema: Type[BaseModel] = GetAvailableDocsInput

    def _run(self, query: str = "all") -> str:
        """Return all available PlantUML documentation links"""
        docs_list = "📚 AVAILABLE PLANTUML DOCUMENTATION\n"
        docs_list += "=" * 60 + "\n\n"

        for diagram_type, url in PLANTUML_DOCS.items():
            docs_list += f"• {diagram_type.upper():<15} → {url}\n"

        docs_list += "\n" + "=" * 60
        docs_list += "\n💡 Use 'Fetch PlantUML Documentation' tool with the diagram type to get syntax examples."

        return docs_list


# Initialize tools
fetch_docs_tool = FetchPlantUMLDocsTool()
get_docs_tool = GetAvailableDocsTool()

# ============================================
# AGENTS
# ============================================

# Agent 1: Documentation Selector
doc_selector = Agent(
    role="Documentation Specialist",
    goal="Identify the correct PlantUML diagram type and fetch relevant documentation",
    backstory="""You are an expert at understanding user requirements and mapping them to 
    the correct PlantUML diagram type. You have access to official PlantUML documentation 
    and can fetch the right syntax guide for any diagram type.

    When given a user request:
    1. First, identify what type of diagram they need
    2. Use the 'Get Available Documentation Links' tool to see all options
    3. Use the 'Fetch PlantUML Documentation' tool to get syntax for that specific type
    4. Return the documentation with clear examples""",
    tools=[fetch_docs_tool, get_docs_tool],
    llm=llm,
    verbose=True,
    allow_delegation=False
)

# Agent 2: UML Generator
uml_generator = Agent(
    role="UML Diagram Code Generator",
    goal="Generate syntactically correct PlantUML code based on official documentation and user requirements",
    backstory="""You are an expert UML designer who creates valid PlantUML code. 
    You ALWAYS follow the official PlantUML syntax from the documentation provided.

    CRITICAL RULES:
    1. ALWAYS start with @startuml and end with @enduml
    2. For activity diagrams with swimlanes: Define swimlane BEFORE 'start' keyword
       Example: |User| then start
    3. Use modern PlantUML syntax (not old beta syntax like (*))
    4. Follow the EXACT syntax patterns from the official documentation
    5. Output ONLY the PlantUML code wrapped in @startuml...@enduml, NO explanations
    6. Do NOT use markdown code blocks, just raw PlantUML code

    When you receive documentation, study the examples carefully and replicate the syntax style.""",
    llm=llm,
    verbose=True,
    allow_delegation=False
)

# Agent 3: Syntax Validator & Fixer
syntax_validator = Agent(
    role="PlantUML Syntax Validator and Fixer",
    goal="Validate PlantUML code against official documentation and fix any syntax errors",
    backstory="""You are a meticulous code reviewer specializing in PlantUML syntax. 
    You compare generated code against official PlantUML documentation and identify 
    syntax errors. 

    Common errors you fix:
    - Missing @startuml or @enduml tags
    - Incorrect swimlane definitions (must be before 'start')
    - Old syntax usage ((*) instead of start/stop)
    - Improper arrow or connection syntax
    - Missing semicolons after actions

    You have access to documentation tools and can fetch syntax guides to verify corrections.

    Output format:
    - If code is valid: "VALID" followed by the original code
    - If code has errors: Output the CORRECTED code with fixes applied""",
    tools=[fetch_docs_tool],
    llm=llm,
    verbose=True,
    allow_delegation=False
)


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_diagram_type(prompt: str) -> str:
    """Detect diagram type from user prompt"""
    prompt_lower = prompt.lower()

    type_keywords = {
        "use case": ["use case", "usecase", "actor", "user story"],
        "activity": ["activity", "workflow", "process flow", "action"],
        "sequence": ["sequence", "interaction", "message flow", "timeline"],
        "class": ["class", "object oriented", "inheritance", "uml class"],
        "state": ["state", "state machine", "fsm"],
        "component": ["component", "module", "package"],
    }

    for diagram_type, keywords in type_keywords.items():
        if any(keyword in prompt_lower for keyword in keywords):
            return diagram_type

    return "activity"  # default


def extract_plantuml_code(text: str) -> str:
    """Extract PlantUML code from LLM response"""
    text = text.strip()

    # Remove markdown code blocks
    if "```" in text:
        pattern = r"```(?:plantuml)?\s*(@startuml.*?@enduml)```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()

        parts = text.split("```")
        for part in parts:
            if "@startuml" in part:
                code = part.replace("plantuml", "").strip()
                return code

    # Look for @startuml...@enduml
    pattern = r"(@startuml.*?@enduml)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()

    return text


def save_uml_locally(uml_code: str, filename="diagram_code.png") -> bool:
    """Save UML diagram by sending code to PlantUML API"""
    url = "https://plantumlgen.pythonanywhere.com/generate_uml"

    try:
        print(f"📤 Sending UML code to rendering API...")
        response = requests.post(url, data={"uml_text": uml_code}, timeout=30)

        if response.status_code != 200:
            response = requests.get(url, params={"uml_text": uml_code}, timeout=30)

        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)
                print(f"✅ Diagram saved as {filename}")
            return True
        else:
            print(f"❌ API Error: Status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error saving diagram: {e}")
        return False


# ============================================
# MAIN GENERATION FUNCTION
# ============================================

def generate_and_render_uml(user_prompt: str, max_retries=2):
    """Generate UML with documentation-based validation"""

    # STEP 1: Identify diagram type and fetch documentation
    print("\n" + "=" * 70)
    print("STEP 1: IDENTIFYING DIAGRAM TYPE & FETCHING DOCUMENTATION")
    print("=" * 70)

    diagram_type = get_diagram_type(user_prompt)
    print(f"🔍 Auto-detected diagram type: {diagram_type.upper()}")

    doc_task = Task(
        description=f"""Analyze this user request and fetch the appropriate PlantUML documentation:

USER REQUEST: "{user_prompt}"

Detected diagram type: {diagram_type}

Tasks:
1. Confirm if '{diagram_type}' is the correct diagram type for this request
2. Use 'Fetch PlantUML Documentation' tool to get official syntax for this diagram type
3. Return the complete documentation with syntax examples

Be thorough - the next agent will use this documentation to generate code.""",
        expected_output="Complete PlantUML syntax documentation with examples from the official website",
        agent=doc_selector
    )

    doc_crew = Crew(
        agents=[doc_selector],
        tasks=[doc_task],
        verbose=True
    )

    doc_result = doc_crew.kickoff()
    documentation = doc_result.raw

    print(f"\n✅ Documentation retrieved successfully")
    print(f"📄 Preview: {documentation[:300]}...\n")

    # STEP 2: Generate UML code using documentation
    for attempt in range(max_retries):
        print("\n" + "=" * 70)
        print(f"STEP 2: GENERATING PLANTUML CODE (Attempt {attempt + 1}/{max_retries})")
        print("=" * 70)

        try:
            gen_task = Task(
                description=f"""Generate PlantUML code for this user request:

USER REQUEST: "{user_prompt}"

OFFICIAL DOCUMENTATION TO FOLLOW:
{documentation}

CRITICAL REQUIREMENTS:
1. Study the documentation examples carefully
2. Start with @startuml and end with @enduml
3. For activity diagrams with swimlanes: Define swimlane BEFORE 'start' (e.g., |User| then start)
4. Follow the EXACT syntax patterns from the documentation
5. Output ONLY the PlantUML code - no explanations, no markdown blocks
6. The code must be complete and ready to render

Generate the code now:""",
                expected_output="Complete PlantUML code following official syntax, wrapped in @startuml...@enduml",
                agent=uml_generator
            )

            gen_crew = Crew(
                agents=[uml_generator],
                tasks=[gen_task],
                verbose=True
            )

            gen_result = gen_crew.kickoff()
            uml_code = extract_plantuml_code(gen_result.raw)

            print(f"\n✅ Code generated")
            print(f"📝 Code length: {len(uml_code)} characters\n")

            # STEP 3: Validate and fix if needed
            print("\n" + "=" * 70)
            print("STEP 3: VALIDATING & FIXING SYNTAX")
            print("=" * 70)

            validation_task = Task(
                description=f"""Validate this PlantUML code and fix any syntax errors:

CODE TO VALIDATE:
{uml_code}

DIAGRAM TYPE: {diagram_type}

Validation checklist:
1. Has @startuml at start and @enduml at end?
2. If activity diagram with swimlanes: Is swimlane defined BEFORE 'start'?
3. Uses modern syntax (not old (*) syntax)?
4. Follows the official documentation patterns?
5. Has proper semicolons, arrows, and syntax?

If you find errors:
- Fetch the documentation using 'Fetch PlantUML Documentation' tool
- Fix the errors based on official syntax
- Output the CORRECTED code

If code is valid:
- Output: VALID
- Then output the original code

Validate now:""",
                expected_output="Either 'VALID' with original code, or corrected PlantUML code",
                agent=syntax_validator
            )

            val_crew = Crew(
                agents=[syntax_validator],
                tasks=[validation_task],
                verbose=True
            )

            val_result = val_crew.kickoff()
            validation_output = val_result.raw

            # Check validation result
            if "VALID" in validation_output.upper()[:50]:
                print("✅ Syntax validation passed!")
                final_code = uml_code
            else:
                print("🔧 Code was corrected by validator")
                final_code = extract_plantuml_code(validation_output)

            # STEP 4: Save diagram
            print("\n" + "=" * 70)
            print("STEP 4: RENDERING & SAVING DIAGRAM")
            print("=" * 70)
            print(f"\n📋 Final PlantUML Code:\n")
            print(final_code)
            print()

            if save_uml_locally(final_code):
                return final_code
            else:
                print("⚠️ Failed to save diagram, but code is valid")
                return final_code

        except Exception as e:
            print(f"❌ Error during generation: {e}")
            if attempt < max_retries - 1:
                print("🔄 Retrying with fresh attempt...")
                continue
            else:
                print("❌ Max retries reached")

    # FALLBACK: Use template
    print("\n⚠️ All attempts failed. Using fallback template...")
    fallback_code = UML_TEMPLATES.get(diagram_type, UML_TEMPLATES["activity"])
    print(f"\n📋 Fallback {diagram_type} template:\n{fallback_code}\n")
    save_uml_locally(fallback_code, "diagram_fallback.png")
    return fallback_code


# ============================================
# MAIN EXECUTION
# ============================================

if __name__ == "__main__":
    print("🤖 CREWAI UML GENERATOR WITH DOCUMENTATION-BASED VALIDATION")
    print("=" * 70)
    print("This system uses 3 AI agents:")
    print("  1. Documentation Specialist - Fetches official PlantUML syntax")
    print("  2. UML Code Generator - Creates diagrams using official patterns")
    print("  3. Syntax Validator - Verifies and fixes any errors")
    print("=" * 70)

    user_request = input("\n📝 Enter your UML diagram request:\n> ").strip()

    if not user_request:
        user_request = "Create an activity diagram for a gen AI hub where admin manages users and user can chat with AI"
        print(f"\n💡 Using example: {user_request}")

    final_code = generate_and_render_uml(user_request)

    print("\n" + "=" * 70)
    print("✅ PROCESS COMPLETE!")
    print("=" * 70)
    print("\n📄 Final PlantUML Code:")
    print("-" * 70)
    print(final_code)
    print("-" * 70)
    print("\n💾 Check your directory for the generated diagram image!")

# ============================================
# EXAMPLE PROMPTS TO TRY
# ============================================
"""
Example prompts:
1. "Create a use case diagram for a login system with user and admin actors"
2. "Generate an activity diagram for a gen AI hub where admin manages users and user can chat with AI"
3. "Make a sequence diagram showing API authentication flow"
4. "Create a class diagram for a user management system"
5. "Design a component diagram for a microservices architecture"
"""
#i want to generate a use case diagram where anyone can fill their mail id password and admin will verify and let them access dashboard
#generate a usecase diagram for a gen ai hub whereadmin will Manage users Deploy / Monitor AI models Update agent logic Manage API keys and datasets View usage analytics  and user can Login/Register Chat with AI Agents Summarize content (YouTube/web/article) Use Medical Assistant Use Character Chat Generate creative content (text, image) View AI analytics or history

