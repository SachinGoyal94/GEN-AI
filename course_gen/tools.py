import os

from crewai.tools import BaseTool
from langchain_community.utilities.tavily_search import TAVILY_API_URL

from llm import gemini_llm
# Custom tool to fetch Skills required from the llm

from langchain_tavily import TavilySearch
os.environ["TAVILY_API_KEY"]=os.getenv('TAVILY_KEY')

class SkillDiscovery(BaseTool):
    name: str = "Skill Discovery Search Tool"
    description: str = (
        "Fetches the skills required to master the given topic or course"
    )

    def _run(self, course: str) -> str:
        print(f"--- Searching skills for course: {course} ---")
        prompt=(f"You are an expert in carrer coaching and a top quality educator. \n "
                f"list all the skills that one must possess to achieve the mastery in topic:{course} \n"
                f"Return them as a numbered list grouped by skill areas.")
        try:
            tool = TavilySearch(topic='general', max_results=5)
            response = tool.invoke({"query": prompt})

            return response
        except Exception as e:
            print(e)
Skill_tool = SkillDiscovery()

#Custom tool to fetch the content from the Wikipedia

from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import  WikipediaAPIWrapper
from langchain_core.prompts import MessagesPlaceholder

wiki_api_wrapper=WikipediaAPIWrapper(top_k_results=1,doc_content_chars_max=10000)
wiki_tool=WikipediaQueryRun(api_wrapper=wiki_api_wrapper)


class Wiki_Content(BaseTool):
    name: str = "Content Search Tool"
    description: str = (
        "Fetches the content required to master the given topic or course from the Wikipedia"
    )

    def _run(self, course: str) -> str:
        return wiki_tool.run(course)
WikiPedia_tool = Wiki_Content()

class Notesmaker(BaseTool):
    name: str = "Notes maker Tool"
    description: str = (
        "Creates the notes required to master the given topic or course"
    )

    def _run(self, course: str) -> str:
        prompt=( f"""You are an expert educator creating detailed teaching content.
        
        Create comprehensive teaching material for: {course}
        
        Structure your response as follows:
        1. INTRODUCTION (1 paragraph explaining what this topic is)
        2. KEY CONCEPTS (List and explain 5-7 main concepts)
        3. DETAILED EXPLANATION (Step-by-step breakdown)
        4. PRACTICAL EXAMPLES (3-4 real-world examples with code if applicable)
        5. COMMON MISCONCEPTIONS (What students often get wrong)
        6. PREREQUISITES (What to know before learning this)
        7. LEARNING PROGRESSION (Beginner → Intermediate → Advanced)
        8. PRACTICE EXERCISES (5 hands-on exercises)
        9. FURTHER READING (Resources for deeper learning)
        
        Make it detailed enough for a 30-45 minute teaching session.
        Include analogies and simple explanations for complex concepts.
        """)
        try:
            response=gemini_llm.predict(prompt).strip()
            return response
        except Exception as e:
            print(e)
Notes_tool=Notesmaker()

class Quiz_maker(BaseTool):
    name: str = "Quiz maker Tool"
    description: str = (
        "Creates the Quiz required to test the knowledge of the learner based on the given topic or course"
    )

    def _run(self, course: str) -> str:
        prompt=(f"You are an expert in making knowledge testing quizzes for any topic . \n "
                f"list all the quizzes that one must answer to test  the mastery in topic:{course} \n"
                f"Remember you should create basic questions of each topic to master ones and based on the content."
                f"if it's related to practical knowledge then provide more pracitcal questions"
                f"Return them as a numbered list but do mention the topic with the answer key at the end")
        try:
            response=gemini_llm.predict(prompt).strip()
            return response
        except Exception as e:
            print(e)
Quiz_tool=Quiz_maker()