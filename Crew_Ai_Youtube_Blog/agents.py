# Youtube Blog Poster Creator Agents

# a senior blog content researcher agent explores yt channel and uses yt tools to get info like transcriptios
# from yt video and then pass it to the content creator to create the content from the info recieved and then
# it will create the content
#the whole process will be sequential from researcher to writer not both agents will be working together


from crewai import Agent
from tools import yt_tool
from llm import gemini_llm
import os
from dotenv import load_dotenv
load_dotenv()

#Creating a Senior Blog Content Researcher
blog_researcher=Agent(
    role="Blog Researcher from youtube videos",
    goal="get the relevant video transcription for the topic {topic} from the provided Youtube Channel",
    verbose=True,
    memory=True,
    backstory="Ai Data Science and Gen ai Expert in understanding Youtube videos",
    tools=[yt_tool],
    allow_delegation=True,  #to pass the info to the further agents here content writer
    llm=gemini_llm
)

blog_writer=Agent(
    role="Blog writer",
    goal="Narrate compelling tech stories from yt video {topic} from Youtube",
    verbose=True,
    memory=True,
    backstory=(
            "With a flair for simplifying complex topics, you craft"
            "engaging narratives that captivate and educate, bringing new"
            "discoveries to light in an accessible manner."
        ),
    tools=[yt_tool],
    allow_delegation=False, #No need to pass info to anyone
    llm=gemini_llm
)