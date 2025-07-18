from crewai import Crew, Process
from agents import create_character_agent
from tasks import create_character_response_task
from tools import set_character_context


def build_character_crew(character_name: str, character_summary: str, user_message: str, llm):
    """Build a crew for character interaction."""

    # Set the character context for the tool
    set_character_context(character_name, character_summary)

    # Create the character agent
    agent = create_character_agent(character_name, character_summary, llm)

    # Create the response task
    task = create_character_response_task(character_name, user_message, agent)

    # Create and return the crew
    return Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
        memory=False
    )