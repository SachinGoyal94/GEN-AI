from crewai import Agent
from gov_llm import gemini_llm
from gov_tools import excel_tool, doc_tool

policy_researcher = Agent(
    role="Policy Researcher",
    goal="Analyze datasets and documents to summarize evidence for policy-making.",
    backstory="Expert researcher in government policy, economics, and data-driven decision making.",
    tools=[excel_tool, doc_tool],
    llm=gemini_llm,
    verbose=True,
    memory=True,
    allow_delegation=True
)

policy_maker = Agent(
    role="Policy Maker",
    goal="Draft actionable policies based on research findings.",
    backstory="Senior government policy maker experienced in drafting national programs.",
    tools=[doc_tool],
    llm=gemini_llm,
    verbose=True,
    memory=True,
    allow_delegation=True
)

policy_critic = Agent(
    role="Policy Critic",
    goal="Review policy drafts for risks, feasibility, and improvements.",
    backstory="Analyst specializing in governance, impact, and risk assessment.",
    tools=[doc_tool],
    llm=gemini_llm,
    verbose=True,
    memory=True,
    allow_delegation=False
)
