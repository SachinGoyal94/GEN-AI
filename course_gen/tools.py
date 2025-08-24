import os
from crewai.tools import BaseTool
from langchain_community.utilities.tavily_search import TAVILY_API_URL
from llm import gemini_llm
from langchain_tavily import TavilySearch
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

os.environ["TAVILY_API_KEY"] = os.getenv('TAVILY_KEY')


class SkillDiscovery(BaseTool):
    name: str = "Skill Discovery Search Tool"
    description: str = (
        "Fetches the skills required to master the given topic or course"
    )

    def _run(self, course: str) -> str:
        print(f"--- Searching skills for course: {course} ---")
        prompt = (f"You are an expert in career coaching and a top quality educator. \n "
                  f"list all the skills that one must possess to achieve the mastery in topic:{course} \n"
                  f"Return them as a numbered list grouped by skill areas.")
        try:
            tool = TavilySearch(topic='general', max_results=5)
            response = tool.invoke({"query": prompt})
            return response
        except Exception as e:
            print(e)
            return f"Error fetching skills: {str(e)}"


Skill_tool = SkillDiscovery()

# Enhanced Wikipedia tool
wiki_api_wrapper = WikipediaAPIWrapper(top_k_results=3, doc_content_chars_max=15000)
wiki_tool = WikipediaQueryRun(api_wrapper=wiki_api_wrapper)


class Wiki_Content(BaseTool):
    name: str = "Content Search Tool"
    description: str = (
        "Fetches comprehensive content from Wikipedia for the given topic"
    )

    def _run(self, course: str) -> str:
        return wiki_tool.run(course)


WikiPedia_tool = Wiki_Content()


class EnhancedNotesmaker(BaseTool):
    name: str = "Enhanced Educational Content Creator"
    description: str = (
        "Creates comprehensive, in-depth educational content by combining web research, "
        "Wikipedia content, and expert knowledge synthesis"
    )

    def _run(self, course: str) -> str:
        print(f"--- Creating enhanced content for: {course} ---")

        # Step 1: Get comprehensive web research
        try:
            search_tool = TavilySearch(topic='general', max_results=8)

            # Multiple targeted searches for different aspects
            searches = [
                f"{course} tutorial comprehensive guide",
                f"{course} best practices examples",
                f"{course} fundamentals concepts explained",
                f"{course} practical applications real world",
                f"{course} common mistakes pitfalls avoid"
            ]

            research_data = ""
            for search_query in searches:
                try:
                    search_result = search_tool.invoke({"query": search_query})
                    research_data += f"\n--- Research for: {search_query} ---\n{search_result}\n"
                except Exception as e:
                    print(f"Search failed for {search_query}: {e}")
                    continue

            # Step 2: Get Wikipedia content
            wiki_content = ""
            try:
                wiki_content = wiki_tool.run(course)
            except Exception as e:
                print(f"Wikipedia search failed: {e}")

            # Step 3: Create comprehensive content using all sources
            enhanced_prompt = f"""
You are a world-class educational content creator and expert instructor. 
Create the most comprehensive, engaging, and practical educational material for: {course}

AVAILABLE RESEARCH DATA:
{research_data}

WIKIPEDIA REFERENCE:
{wiki_content}

Your task is to synthesize ALL this information into exceptional educational content.

STRUCTURE YOUR RESPONSE AS FOLLOWS:

🎯 **COURSE OVERVIEW**
- What is {course}?
- Why is it important in today's world?
- Career opportunities and applications
- Industry demand and trends

📚 **FUNDAMENTAL CONCEPTS** 
- Core principles (explain each in detail)
- Essential terminology with clear definitions  
- Conceptual framework and mental models
- How concepts interconnect

🔧 **TECHNICAL DEEP DIVE**
- Step-by-step methodology
- Tools and technologies involved
- Best practices from industry experts
- Latest trends and emerging technologies

💡 **PRACTICAL EXAMPLES & CASE STUDIES**
- Real-world applications with detailed explanations
- Code examples (if applicable) with line-by-line breakdown
- Industry case studies
- Success stories and lessons learned

⚠️ **COMMON CHALLENGES & SOLUTIONS**
- Typical beginner mistakes and how to avoid them
- Advanced pitfalls and troubleshooting
- Performance optimization tips
- Debug strategies

🎓 **LEARNING PATHWAY**
- **Beginner Level**: Foundation building (weeks 1-2)
- **Intermediate Level**: Skill development (weeks 3-6) 
- **Advanced Level**: Mastery and specialization (weeks 7-12)
- Prerequisites for each level

🛠️ **HANDS-ON PROJECTS & EXERCISES**
- 5 Progressive projects from basic to advanced
- Step-by-step project guides
- Skills assessment checkpoints
- Portfolio-worthy deliverables

📖 **COMPREHENSIVE RESOURCES**
- Essential books and documentation
- Online courses and certifications
- Communities and forums
- Tools and software recommendations
- Industry blogs and thought leaders

🌟 **EXPERT INSIGHTS & TIPS**
- Industry secrets and insider knowledge
- Networking opportunities
- Interview preparation advice
- Salary expectations and negotiation tips

Make this content so comprehensive and engaging that it could serve as a complete course curriculum. 
Include analogies, real-world connections, and actionable advice throughout.
Aim for content that takes 60-90 minutes to thoroughly review and understand.
"""

            # Generate enhanced content
            response = gemini_llm.predict(enhanced_prompt).strip()

            # Add metadata
            final_content = f"""
# 📚 COMPREHENSIVE EDUCATIONAL CONTENT: {course.upper()}

Generated on: {self._get_timestamp()}
Content Quality: Enhanced with Web Research + Wikipedia Integration
Estimated Study Time: 60-90 minutes

{response}

---
📊 **CONTENT SOURCES UTILIZED:**
- Live web research from multiple educational sources
- Wikipedia comprehensive coverage
- Industry best practices synthesis  
- Expert knowledge compilation

💬 **LEARNING SUPPORT:**
For questions or clarification on any topic, refer back to the specific sections above.
Practice the exercises in order for optimal learning progression.
"""

            return final_content

        except Exception as e:
            print(f"Enhanced content creation failed: {e}")
            # Fallback to basic content generation
            return self._create_basic_content(course)

    def _create_basic_content(self, course: str) -> str:
        """Fallback method for basic content creation"""
        basic_prompt = f"""
Create detailed educational content for {course}.
Include: introduction, key concepts, examples, best practices, and learning resources.
Make it comprehensive and practical for students.
"""
        return gemini_llm.predict(basic_prompt).strip()

    def _get_timestamp(self):
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# Create the enhanced tool instance
Notes_tool = EnhancedNotesmaker()


class Quiz_maker(BaseTool):
    name: str = "Enhanced Quiz Creator"
    description: str = (
        "Creates comprehensive quizzes with multiple difficulty levels to test knowledge"
    )

    def _run(self, course: str) -> str:
        prompt = f"""
You are an expert educational assessment creator. Create a comprehensive quiz for: {course}

QUIZ REQUIREMENTS:
- 25 questions total across 3 difficulty levels
- Include multiple choice, multiple select, and scenario-based questions
- Cover both theoretical knowledge and practical application
- Provide detailed explanations for each answer

STRUCTURE:
🟢 **BEGINNER LEVEL (Questions 1-8)**
- Fundamental concepts and terminology
- Basic understanding checks

🟡 **INTERMEDIATE LEVEL (Questions 9-17)**  
- Application of concepts
- Problem-solving scenarios

🔴 **ADVANCED LEVEL (Questions 18-25)**
- Complex scenarios and best practices
- Industry-level challenges

FORMAT EACH QUESTION AS:
**Question X:** [Question text]
A) Option A
B) Option B  
C) Option C
D) Option D
[For multiple select: "Select all that apply"]

END WITH COMPLETE ANSWER KEY:
**ANSWER KEY & EXPLANATIONS:**
1. Answer: [Letter] - [Detailed explanation why this is correct and others are wrong]
...

Make questions practical and relevant to real-world {course} applications.
"""
        try:
            response = gemini_llm.predict(prompt).strip()
            return response
        except Exception as e:
            print(e)
            return f"Error creating quiz: {str(e)}"


Quiz_tool = Quiz_maker()