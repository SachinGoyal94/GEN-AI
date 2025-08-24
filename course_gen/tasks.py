from crewai import Task
from curriculum_agent import curriculum_creator_agent,content_writer,quiz_maker
from tools  import Skill_tool,WikiPedia_tool,Notes_tool,Quiz_tool
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
        """
    For each topic identified in the topic breakdown, create comprehensive teaching content.
    
    Use the Detailed Topic Content Extractor tool for EACH individual topic.
    Create content that includes:
    1. Comprehensive explanations
    2. Practical examples
    3. Common misconceptions 
    4. Practice exercises
    5. Learning progression
    
    Ensure content is detailed enough for 30-45 minute teaching sessions per topic.
    """),
    expected_output="Comprehensive teaching content for every topic and subtopic",
    tools=[Notes_tool],
    agent=content_writer,
    context=[skill_research_task]
)

Quiz_creator_task=Task(
    description=(
        "Identify the most important aspects of the course"
        "create a quiz based on the content provided"
        "\n\n Important Instructions:"
        "1: The Question should be relevant to topic and the content"
        "2: you should give 4 options "
        "3: Do create multi choice questions"
        "4: Do not forget to provide answers as the answer sheet at the end"
    ),
    expected_output=(
        "A perfect quiz with four options some including multi choice also"
        "that can test the knowledge of the learners "
        "if it's related to practical knowledge then provide more pracitcal questions"
        "Return them as a numbered list but do mention the topic with the answer key at the end of all the questions completion"
    ),
    tools=[Quiz_tool],
    agent=quiz_maker,
    context=[content_research_task]
)