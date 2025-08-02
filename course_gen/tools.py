#from crewai_tools import YoutubeChannelSearchTool
#yt_tool = YoutubeChannelSearchTool(youtube_channel_handle='@krishnaik06')
#the above code is not working so  creating a custom tool
from typing import Type
from pydantic import BaseModel, Field
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
        prompt=(f"You are an expert in carrerr coaching and a top quality educator. \n "
                f"list all the skills that one must possess to achieve the mastery in topic:{course} \n"
                f"Return them as a numbered list grouped by skill areas.")
        try:
            response=gemini_llm.predict(prompt).strip
        except Exception as e:
            print(e)
Skill_tool = SkillDiscovery()

#Custom tool to fetch the content from the Wikipedia

from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import  WikipediaAPIWrapper
from langchain_core.prompts import MessagesPlaceholder

wiki_api_wrapper=WikipediaAPIWrapper(top_k_results=1,doc_content_chars_max=10000)
wiki_tool=WikipediaQueryRun(api_wrapper=wiki_api_wrapper)


class WikiContentInput(BaseModel):
    query: str = Field(..., description="The topic, skill, or course to search for content")


class Wiki_Content(BaseTool):
    name: str = "Content Search Tool"
    description: str = (
        "Fetches educational content from Wikipedia for specific skills. "
        "Can search for individual skills or a comma-separated list of skills. "
        "Use this to get detailed content for each skill identified by the curriculum creator."
    )
    args_schema: Type[BaseModel] = WikiContentInput

    def _run(self, query: str) -> str:
        try:
            print(f"--- Searching Wikipedia for: {query} ---")

            # Check if query contains multiple skills (comma-separated)
            if "," in query:
                skills = [skill.strip() for skill in query.split(",") if skill.strip()]
                print(f"Found {len(skills)} skills to search for")

                all_content = []
                for i, skill in enumerate(skills[:8], 1):  # Limit to 8 skills to avoid too much content
                    print(f"Searching for skill {i}: {skill}")
                    try:
                        skill_content = wiki_tool.run(skill)
                        all_content.append(
                            f"\n{'=' * 50}\n{i}. CONTENT FOR SKILL: {skill.upper()}\n{'=' * 50}\n{skill_content}")
                    except Exception as e:
                        all_content.append(
                            f"\n{'=' * 50}\n{i}. CONTENT FOR SKILL: {skill.upper()}\n{'=' * 50}\nError fetching content: {str(e)}")

                return "\n".join(all_content)

            else:
                # Single skill or topic
                content = wiki_tool.run(query)
                return f"{'=' * 50}\nCONTENT FOR: {query.upper()}\n{'=' * 50}\n{content}"

        except Exception as e:
            print(f"Error fetching Wikipedia content: {e}")
            return f"Failed to fetch Wikipedia content for {query}: {str(e)}"


WikiPedia_tool = Wiki_Content()
