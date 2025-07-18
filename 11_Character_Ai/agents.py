from crewai import Agent
from tools import character_tool


def create_character_agent(character_name: str, character_summary: str, llm):
    """Create a character agent that can respond in character."""

    return Agent(
        name=f"{character_name} Character Agent",
        role=f"Character roleplay specialist for {character_name}",
        goal=f"Respond authentically as {character_name}, maintaining their personality, speech patterns, and behavioral traits",
        backstory=f"""
        You are {character_name}. Here is your character information:

        {character_summary}

        Your task is to respond to user messages exactly as {character_name} would respond.
        Stay true to the character's personality, use their typical speech patterns, 
        and maintain consistency with their established traits and background.
        """,
        tools=[character_tool],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        memory=False,
        max_iter=3
    )