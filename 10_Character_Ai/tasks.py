from crewai import Task
from tools import character_tool


def create_character_response_task(character_name: str, user_message: str, agent):
    """Create a task for the character to respond to the user's message."""

    return Task(
        description=f"""
        You are {character_name}. The user has sent you this message: "{user_message}"

        Your task is to respond exactly as {character_name} would respond to this message.

        Guidelines:
        1. Stay completely in character as {character_name}
        2. Use their typical speech patterns and vocabulary
        3. Respond based on their personality traits and background
        4. Be authentic to how {character_name} would actually react
        5. If you need more information about the character, use the Character Information Tool

        Respond naturally and conversationally as {character_name}.
        """,
        expected_output=f"""
        A natural, authentic response from {character_name} to the user's message.
        The response should:
        - Sound like {character_name} is actually speaking
        - Reflect their personality and character traits
        - Be appropriate to their background and context
        - Feel like a genuine conversation
        """,
        tools=[character_tool],
        agent=agent
    )