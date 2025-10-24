import os
import requests
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, LLM
import urllib.parse
load_dotenv()
mistral_key = os.getenv("MISTRAL_KEY")

llm = LLM(
    model="mistral/mistral-large-latest",
    api_key=mistral_key
)

uml_generator = Agent(
    role="UML Diagram Generator",
    goal="Generate syntactically correct PlantUML code based on user requests.",
    backstory="An expert UML designer who creates valid PlantUML code for class, use case, activity, and sequence diagrams.",
    llm=llm
)
def save_uml_locally(uml_code: str, filename="merioutput.png") -> None:

    url = "https://plantumlgen.pythonanywhere.com/generate_uml"
    uml_text = uml_code
    encoded_text = urllib.parse.quote(uml_text)
    params = {"uml_text": encoded_text}
    response = requests.get(url, params=params)

    try:
        if response.status_code == 200:
            output_path = os.path.join(os.getcwd(), filename)
            with open(output_path, "wb") as f:
                try:
                    f.write(response.content)
                    print(f"✅ Diagram saved as {filename}")
                except Exception as e:
                    print(e)
    except Exception as ex:
        print(ex)

def generate_and_render_uml(user_prompt: str):
    task = Task(
        description=f"Generate PlantUML code for this user request: {user_prompt}",
        expected_output="Valid PlantUML code wrapped between @startuml and @enduml tags.",
        agent=uml_generator
    )

    crew = Crew(
        agents=[uml_generator],
        tasks=[task],
        verbose=True
    )

    print("🧠 Generating UML code...")
    result = crew.kickoff()
    uml_code = result.raw.strip()

    print("\n✅ Generated PlantUML Code:\n")
    print(uml_code)
    print("\n🖼️ Saving diagram locally...")
    save_uml_locally(uml_code)
    return uml_code

if __name__ == "__main__":
    print("🤖 CrewAI UML Diagram Generator")
    user_request = input("Enter your UML request (e.g., 'create a use case diagram for login system'): ")
    generate_and_render_uml(user_request)

#Sample Problems
#i want to generate a use case diagram where anyone can fill their mail id password and admin will verify and let them access dashboard
#generate a swimlane diagram for a gen ai hub whereadmin will Manage users Deploy / Monitor AI models Update agent logic Manage API keys and datasets View usage analytics  and user can Login/Register Chat with AI Agents Summarize content (YouTube/web/article) Use Medical Assistant Use Character Chat Generate creative content (text, image) View AI analytics or history
