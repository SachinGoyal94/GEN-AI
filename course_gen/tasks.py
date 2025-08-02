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
        "find the content required to master the  {course}"),
    expected_output="Comprehensive content outline and learning materials for {course}",
    tools=[WikiPedia_tool],
    agent=content_writer
)