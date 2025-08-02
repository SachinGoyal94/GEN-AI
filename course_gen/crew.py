from crewai import Crew, Process
from tasks import skill_research_task,content_research_task
from curriculum_agent import curriculum_creator_agent,content_writer
from llm import gemini_llm
from tools import Skill_tool,WikiPedia_tool


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
    agents=[curriculum_creator_agent,content_writer],
    tasks=[skill_research_task,content_research_task],
    process=Process.sequential,
    verbose=True,
)

result = crew.kickoff(inputs={'course': 'Data Structures'})
print(result)