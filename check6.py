import os
import base64
import requests
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, LLM
from typing import Optional

load_dotenv()
mistral_key = os.getenv("MISTRAL_KEY")
if not mistral_key:
    raise ValueError("❌ MISTRAL_KEY missing in .env file")

llm = LLM(
    model="mistral/mistral-large-latest",
    api_key=mistral_key
)

# Agent 1: UML Generator
uml_generator = Agent(
    role="UML Diagram Generator",
    goal="Generate syntactically correct PlantUML code based on user requests and feedback.",
    backstory="""You are an expert UML designer who creates valid PlantUML code for various diagram types.

    CRITICAL RULES:
    1. ALWAYS start with @startuml and end with @enduml
    2. For activity diagrams with swimlanes: Define swimlane BEFORE 'start' (e.g., |User| then start)
    3. Use modern PlantUML syntax (not old (*) syntax)
    4. For flowcharts, use activity diagram syntax
    5. Output ONLY PlantUML code, no explanations
    6. If you receive feedback about errors, fix them and regenerate

    When given feedback, carefully analyze what went wrong and correct it.""",
    llm=llm,
    verbose=True
)

# Agent 2: Image Validator using Vision Model
image_validator = Agent(
    role="Diagram Visual Validator",
    goal="Analyze generated diagram images and validate if they match user requirements",
    backstory="""You are an expert at analyzing UML diagrams visually. You can:
    - Identify what type of diagram is shown
    - Verify if all required elements are present
    - Check if the diagram structure is correct
    - Spot missing actors, actions, or connections
    - Provide specific feedback on what needs to be fixed

    You provide detailed, actionable feedback to help improve the diagram.""",
    llm=llm,
    verbose=True
)


def encode_image_to_base64(image_path: str) -> str:
    """Encode image file to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def validate_diagram_with_vision(image_path: str, user_request: str, mistral_key: str) -> dict:
    """
    Use Mistral Vision API to analyze the generated diagram
    Returns: dict with 'is_valid' and 'feedback'
    """
    try:
        # Encode image
        base64_image = encode_image_to_base64(image_path)

        # Prepare the API request
        url = "https://api.mistral.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {mistral_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "pixtral-large-latest",  # Mistral's vision model
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""Analyze this UML diagram image and validate if it correctly represents the following user request:

USER REQUEST: "{user_request}"

Please analyze:
1. What type of diagram is this? (use case, activity, sequence, class, etc.)
2. Does it correctly represent the user's requirements?
3. Are all mentioned actors/actions/elements present?
4. Is the diagram structure correct?
5. Are there any syntax errors or missing elements visible?

Provide your response in this format:
VALID: [YES/NO]
DIAGRAM_TYPE: [type]
MISSING_ELEMENTS: [list any missing elements]
ERRORS: [list any visible errors]
SUGGESTIONS: [specific improvements needed]

Be thorough and specific in your analysis."""
                        },
                        {
                            "type": "image_url",
                            "image_url": f"data:image/png;base64,{base64_image}"
                        }
                    ]
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.3
        }

        print("🔍 Analyzing diagram with Mistral Vision API...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            result = response.json()
            analysis = result['choices'][0]['message']['content']

            print(f"\n📊 Vision Analysis Result:\n{analysis}\n")

            # Parse the response
            is_valid = "VALID: YES" in analysis.upper() or "VALID:YES" in analysis.upper()

            return {
                "is_valid": is_valid,
                "feedback": analysis,
                "raw_response": result
            }
        else:
            print(f"❌ Vision API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return {
                "is_valid": False,
                "feedback": f"API Error: {response.status_code}",
                "raw_response": None
            }

    except Exception as e:
        print(f"❌ Error during vision validation: {e}")
        return {
            "is_valid": False,
            "feedback": f"Validation error: {str(e)}",
            "raw_response": None
        }


def save_uml_locally(uml_code: str, filename="merioutput.png") -> bool:
    """Save UML diagram by sending code to PlantUML API"""
    url = "https://plantumlgen.pythonanywhere.com/generate_uml"

    try:
        # Try POST first (better for large code)
        response = requests.post(url, data={"uml_text": uml_code}, timeout=30)

        # Fallback to GET if POST fails
        if response.status_code != 200:
            import urllib.parse
            encoded_text = urllib.parse.quote(uml_code)
            params = {"uml_text": encoded_text}
            response = requests.get(url, params=params, timeout=30)

        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)
                print(f"✅ Diagram saved as {filename}")
            return True
        else:
            print(f"❌ Failed to save diagram. Status: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error saving diagram: {e}")
        return False


def extract_plantuml_code(text: str) -> str:
    """Extract PlantUML code from response"""
    import re
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
                return part.replace("plantuml", "").strip()

    # Look for @startuml...@enduml
    pattern = r"(@startuml.*?@enduml)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()

    return text


def generate_and_render_uml(user_prompt: str, max_iterations=3):
    """Generate UML with vision-based validation and regeneration loop"""

    current_code = None
    feedback_history = []

    for iteration in range(max_iterations):
        print("\n" + "=" * 70)
        print(f"ITERATION {iteration + 1}/{max_iterations}")
        print("=" * 70)

        # STEP 1: Generate or Regenerate UML code
        print("\n🧠 Generating PlantUML code...")

        if iteration == 0:
            # First generation
            task_description = f"""Generate PlantUML code for this user request:

USER REQUEST: "{user_prompt}"

REQUIREMENTS:
1. Start with @startuml and end with @enduml
2. For flowcharts/activity diagrams with swimlanes: Define swimlane BEFORE 'start'
3. Include all elements mentioned in the request
4. Use clear, descriptive labels
5. Ensure proper syntax

Generate the code now:"""
        else:
            # Regeneration with feedback (only if feedback exists)
            previous_feedback = feedback_history[-1] if feedback_history else "No previous feedback"
            task_description = f"""The previous diagram had issues. Please fix and regenerate the PlantUML code.

ORIGINAL USER REQUEST: "{user_prompt}"

PREVIOUS CODE:
{current_code}

FEEDBACK FROM VISUAL ANALYSIS:
{previous_feedback}

Please fix the issues and generate CORRECTED PlantUML code that addresses all the feedback points."""

        generation_task = Task(
            description=task_description,
            expected_output="Valid PlantUML code wrapped between @startuml and @enduml tags.",
            agent=uml_generator
        )

        generation_crew = Crew(
            agents=[uml_generator],
            tasks=[generation_task],
            verbose=True
        )

        result = generation_crew.kickoff()
        current_code = extract_plantuml_code(result.raw.strip())

        print(f"\n✅ Generated PlantUML Code (Iteration {iteration + 1}):\n")
        print(current_code)

        # STEP 2: Render the diagram
        print(f"\n🖼️ Rendering diagram...")
        filename = f"diagram_iteration_{iteration + 1}.png"

        if not save_uml_locally(current_code, filename):
            print("⚠️ Failed to render diagram. Skipping validation.")
            continue

        # STEP 3: Validate with Vision API
        print(f"\n👁️ Validating diagram with Mistral Vision...")

        validation_result = validate_diagram_with_vision(filename, user_prompt, mistral_key)
        feedback_history.append(validation_result['feedback'])

        if validation_result['is_valid']:
            print("\n" + "=" * 70)
            print("✅ DIAGRAM VALIDATED SUCCESSFULLY!")
            print("=" * 70)
            print(f"\n📄 Final Code:\n{current_code}")
            print(f"\n💾 Final diagram saved as: {filename}")
            return current_code, filename
        else:
            print(f"\n⚠️ Validation failed. Issues found:")
            print(validation_result['feedback'])

            if iteration < max_iterations - 1:
                print(f"\n🔄 Attempting regeneration with feedback...")
            else:
                print(f"\n❌ Max iterations reached. Using last generated diagram.")

    # Return last attempt
    print("\n" + "=" * 70)
    print("⚠️ COMPLETED WITH WARNINGS")
    print("=" * 70)
    print("Could not fully satisfy all requirements within iteration limit.")
    print(f"Last generated diagram saved as: diagram_iteration_{max_iterations}.png")

    return current_code, f"diagram_iteration_{max_iterations}.png"


# Main execution
if __name__ == "__main__":
    print("🤖 CREWAI UML GENERATOR WITH VISION-BASED VALIDATION")
    print("=" * 70)
    print("This system:")
    print("  1. Generates PlantUML code based on your request")
    print("  2. Renders the diagram as an image")
    print("  3. Uses Mistral Vision AI to validate the diagram")
    print("  4. Automatically regenerates if issues are found")
    print("=" * 70)

    user_request = input("\n📝 Enter your UML diagram request:\n> ").strip()

    if not user_request:
        user_request = "Create a use case diagram where anyone can fill their mail id password and admin will verify and let them access dashboard"
        print(f"\n💡 Using example: {user_request}")

    final_code, final_image = generate_and_render_uml(user_request)

    print("\n" + "=" * 70)
    print("✅ PROCESS COMPLETE!")
    print("=" * 70)
    print(f"\n📄 Final PlantUML Code:\n{final_code}")
    print(f"\n💾 Image saved as: {final_image}")

# ============================================
# EXAMPLE PROMPTS
# ============================================
"""
Try these prompts:

1. "Create a use case diagram where anyone can fill their mail id password and admin will verify and let them access dashboard"

2. "Generate a flowchart diagram for a gen AI hub where admin will Manage users, Deploy/Monitor AI models, Update agent logic, Manage API keys and datasets, View usage analytics and user can Login/Register, Chat with AI Agents, Summarize content, Use Medical Assistant, Use Character Chat, Generate creative content, View AI analytics or history"

3. "Make a sequence diagram for user authentication with database validation"

4. "Design a class diagram for an e-commerce system with User, Product, and Order classes"
"""