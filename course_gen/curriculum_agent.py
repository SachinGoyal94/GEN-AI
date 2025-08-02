#this is an agent which can help you to create a curriculum for the course you want
import os
from dotenv import load_dotenv
load_dotenv()

os.environ["LANGCHAIN_API_KEY"] = os.getenv('LANGCHAIN_KEY')
os.environ["LANGCHAIN_TRACING_V2"]="true"
os.environ["LANGCHAIN_PROJECT"]="CourseLanggraph"


from crewai import Agent
from tools import Skill_tool,WikiPedia_tool
from llm import gemini_llm

curriculum_creator_agent=Agent(
    role="Curriculum Designer",
    goal="You have to create a perfect curriculum for the course {course}",
    verbose=True,
    memory=True,
    backstory="An Expert in desigining top notch Curriculums in the education industry",
    tools=[Skill_tool],
    allow_delegation=True,
    llm=gemini_llm
)

content_writer=Agent(
    role="Content Creator",
    goal="You have to create a perfect content for the course {course}",
    verbose=True,
    memory=True,
    backstory="An expert in writing the content for any topic given without compromising in the content quality",
    tools=[WikiPedia_tool],
    allow_delegation=True,
    llm=gemini_llm
)

