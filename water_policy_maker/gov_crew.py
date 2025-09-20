# gov_crew.py
# Crew orchestration: researcher -> maker -> critic (sequential)

from crewai import Crew, Process
from gov_agents import policy_researcher, policy_maker, policy_critic
from gov_tasks import research_task, draft_task, critique_task

crew = Crew(
    agents=[policy_researcher, policy_maker, policy_critic],
    tasks=[research_task, draft_task, critique_task],
    process=Process.sequential,
    verbose=True,
)
