from crewai import Task
from gov_agents import policy_researcher, policy_maker, policy_critic
from gov_tools import excel_tool, doc_tool

research_task = Task(
    description="Research datasets and documents to provide evidence on '{policy_problem}'.",
    expected_output="Evidence summary with key stats, trends, and references.",
    agent=policy_researcher,
    tools=[excel_tool, doc_tool]
)

draft_task = Task(
    description="Draft a government policy brief based on research for '{policy_problem}'.",
    expected_output="Structured policy draft with objectives, actions, budget, timeline.",
    agent=policy_maker,
    tools=[doc_tool]
)

critique_task = Task(
    description="Review the draft policy for risks, feasibility, and improvements.",
    expected_output="Risk analysis + suggested improvements.",
    agent=policy_critic,
    tools=[doc_tool]
)
