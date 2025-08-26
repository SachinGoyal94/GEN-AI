from crewai import Crew, Process
from tasks import skill_research_task,content_research_task,Quiz_creator_task,quality_review_task
from curriculum_agent import curriculum_creator_agent,content_writer,quiz_maker,research_analyst_agent,quality_assurance_agent
from llm import gemini_llm
from tools import Skill_tool,WikiPedia_tool,Notes_tool


crew = Crew(
    agents=[curriculum_creator_agent,content_writer,quiz_maker,quality_assurance_agent],
    tasks=[skill_research_task,content_research_task,Quiz_creator_task,quality_review_task],
    process=Process.sequential,
    verbose=True,
)


result = crew.kickoff(inputs={'course': 'Computer Vision'}) #gives only quiz output only

# Get outputs
content_output = str(content_research_task.output.raw)
quiz_output = str(Quiz_creator_task.output.raw)

print("=== CONTENT ===")
print(content_output)
print("\n=== QUIZ ===")
print(quiz_output)

# Save files
course = "Computer Vision"
base = course.replace(' ', '_').lower()

# Individual files
with open(f"data/generated/{base}_content.txt", 'w', encoding='utf-8') as f:
    f.write(content_output)

with open(f"data/generated/{base}_quiz.txt", 'w', encoding='utf-8') as f:
    f.write(quiz_output)

# Combined file
combined = f"""=== CONTENT ===

{content_output}

=== QUIZ ===

{quiz_output}
"""

with open(f"data/generated/{base}_complete.txt", 'w', encoding='utf-8') as f:
    f.write(combined)

print(f"✅ Files saved: {base}_content.txt, {base}_quiz.txt, {base}_complete.txt")