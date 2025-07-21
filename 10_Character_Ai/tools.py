from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type

# Global variable to store the current character summary
_current_character_summary = ""
_current_character_name = ""

def set_character_context(character_name: str, summary: str):
    """Set the current character context for the tool to use."""
    global _current_character_summary, _current_character_name
    _current_character_summary = summary
    _current_character_name = character_name

class CharacterToolInput(BaseModel):
    """Input schema for CharacterTool."""
    query: str = Field(..., description="A question or query about the character's personality, background, or behavior")

class CharacterTool(BaseTool):
    name: str = "Character Information Tool"
    description: str = (
        "Provides detailed information about the character's personality, background, and behavioral traits. "
        "Use this when you need specific details about how the character would behave, speak, or respond."
    )
    args_schema: Type[BaseModel] = CharacterToolInput

    def _run(self, query: str) -> str:
        """Execute the tool with the given query about the character."""
        if _current_character_summary and _current_character_name:
            return f"Character: {_current_character_name}\n\nCharacter Information: {_current_character_summary}\n\nFor your query '{query}': Use this character information to respond authentically as {_current_character_name}."
        else:
            return f"Character context not available. Please refer to the character's backstory in your instructions for query: {query}"

# Create the tool instance
character_tool = CharacterTool()