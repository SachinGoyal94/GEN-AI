from crewai import Crew, Process
from tasks import research_task, write_task
from agents import blog_researcher, blog_writer
from llm import gemini_llm
from tools import yt_tool


#crew = Crew(
#    agents=[blog_researcher, blog_writer],
#    tasks=[research_task, write_task],
#    process=Process.sequential,
#    memory=True,
#    cache=True,
#    max_rpm=100,
#    share_crew=True,
#    llm=gemini_llm
#)

crew = Crew(
    agents=[blog_researcher, blog_writer],
    tasks=[research_task, write_task],
    process=Process.sequential,
    verbose=True,
)

result = crew.kickoff(inputs={'topic': 'AI vs ML vs DL'})
print(result)