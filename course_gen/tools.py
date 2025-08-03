from crewai.tools import BaseTool
from llm import gemini_llm
# Custom tool to fetch Skills required from the llm
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
            response=gemini_llm.predict(prompt).strip()
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
        prompt=(f"You are an expert in making detailed notes for any topic . \n "
                f"list all the notes that one must possess to achieve the mastery in topic:{course} \n"
                f"Remember you should also create basic examples of each topic to master ."
                f"For example if it's related to tech you can provide codes as example"
                f"if it's related to practical knowledge then provide more pracitcal activity content"
                f"Return them as a numbered list grouped by skill areas.")
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