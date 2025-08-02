from crewai import Task
from curriculum_agent import curriculum_creator_agent,content_writer
from tools  import Skill_tool,WikiPedia_tool
from llm import gemini_llm
skill_research_task=Task(
    description=(
        "Identify the skills needed for the topic {course}"),
    expected_output="A list of the skills needed for the topic {course}",
    tools=[Skill_tool],
    agent=curriculum_creator_agent
)

content_research_task=Task(
    description=(
        "Based on the skills identified by the curriculum creator, research and compile "
        "comprehensive learning content for EACH individual skill needed for {course}. "
        "\n\nIMPORTANT INSTRUCTIONS:"
        "\n1. Extract ALL the individual skills from the previous task's output"
        "\n2. For each skill, use the Content Search Tool to find detailed educational content"
        "\n3. You can search for multiple skills by providing them as a comma-separated list to the tool"
        "\n4. Make sure every skill identified gets comprehensive content coverage"
        "\n5. Organize the final output by skill areas for easy learning"
        "\n\nExample: If skills are 'Arrays, Linked Lists, Trees', search for 'Arrays, Linked Lists, Trees'"
    ),
    expected_output=(
        "Comprehensive educational content for EVERY individual skill identified for {course}. "
        "Each skill should have detailed explanations, key concepts, and learning materials. "
        "Content should be organized by skill with clear sections for each topic. "
        "Format: Skill Name -> Detailed Content -> Key Concepts -> Learning Points"
    ),
    tools=[WikiPedia_tool],
    agent=content_writer,
    context=[skill_research_task]
)