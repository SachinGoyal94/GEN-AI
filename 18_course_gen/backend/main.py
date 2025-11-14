import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from crewai import LLM, Agent, Task, Crew
from datetime import datetime
from typing import Type, Any
import time

load_dotenv()

gemini_key = os.getenv("GEMINI_KEY")
if not gemini_key:
    raise ValueError("❌ GEMINI_KEY missing in .env file")

gemini_llm = LLM(
    model="gemini/gemini-2.0-flash",
    api_key=gemini_key
)

tavily_key = os.getenv("TAVILY_KEY")
if not tavily_key:
    raise ValueError("❌ TAVILY_KEY missing in .env file")

os.environ["TAVILY_API_KEY"] = tavily_key

from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools import WikipediaQueryRun
from langchain_tavily import TavilySearch
from crewai.tools import BaseTool


class CourseInput(BaseModel):
    """Input schema for course name"""
    course: str = Field(..., description="The name of the course to analyze")


class AdvancedSkillDiscovery(BaseTool):
    name: str = "Advanced Skill Discovery Tool"
    description: str = "Comprehensive skill analysis with industry trends and certifications. Input: course name as string."
    args_schema: Type[BaseModel] = CourseInput

    def _run(self, course: str) -> str:
        """Run skill discovery analysis"""
        try:
            # Validate input
            if not course or not isinstance(course, str):
                return "Error: Invalid course name provided"

            course = course.strip()
            print(f"🔍 Running skill discovery for: {course}")

            search_tool = TavilySearch(topic="general", max_results=5)
            queries = [
                f"{course} essential skills 2024 industry requirements",
                f"{course} career path roadmap certification",
                f"{course} job market demand salary trends"
            ]

            results = ""
            for q in queries:
                try:
                    time.sleep(0.5)  # Rate limiting
                    search_result = search_tool.invoke({'query': q})
                    results += f"\n=== {q} ===\n{str(search_result)[:800]}\n"
                except Exception as e:
                    print(f"Search error for '{q}': {e}")
                    continue

            analysis_prompt = f"""You are a senior career advisor specializing in {course}.
Based on this research data, create a detailed skills analysis:

{results}

Structure your analysis:

🎯 SKILL CATEGORIES & BREAKDOWN

1. FOUNDATIONAL SKILLS (Must-Have)
- Core concepts every beginner needs
- Basic tools and technologies

2. INTERMEDIATE SKILLS (Career Building)
- Advanced concepts for job readiness
- Popular frameworks and tools

3. ADVANCED/EXPERT SKILLS (Specialization)
- Cutting-edge technologies
- Leadership skills

4. SOFT SKILLS & COMPLEMENTARY ABILITIES
- Communication and collaboration
- Project management

📊 MARKET ANALYSIS
- Current job market demand
- Salary expectations by skill level
- Industry growth trends

🏆 CERTIFICATION & LEARNING PATHS
- Recommended certifications
- Best learning resources
- Timeline expectations

🔮 FUTURE TRENDS & EMERGING SKILLS
- Technologies to watch
- Future-proofing strategies

Keep response comprehensive but under 3000 words."""

            response = gemini_llm.call(analysis_prompt)

            # Handle different response types
            if hasattr(response, 'content'):
                return str(response.content)[:5000]
            return str(response)[:5000]

        except Exception as e:
            error_msg = f"Error during skill discovery: {str(e)[:300]}"
            print(error_msg)
            return error_msg


class MultisourceContentCreator(BaseTool):
    name: str = "Advanced Educational Content Creator"
    description: str = "Creates comprehensive learning content with examples from web and Wikipedia. Input: course name as string."
    args_schema: Type[BaseModel] = CourseInput

    def _run(self, course: str) -> str:
        """Create educational content"""
        try:
            # Validate input
            if not course or not isinstance(course, str):
                return "Error: Invalid course name provided"

            course = course.strip()
            print(f"📚 Creating content for: {course}")

            search_tool = TavilySearch(topic="general", max_results=5)
            data = ""

            for q in [f"{course} tutorial", f"{course} projects", f"{course} advanced guide"]:
                try:
                    time.sleep(0.5)
                    search_result = search_tool.invoke({'query': q})
                    data += f"\n=== {q} ===\n{str(search_result)[:600]}\n"
                except Exception as e:
                    print(f"Search error: {e}")
                    continue

            try:
                wiki_api = WikipediaAPIWrapper(top_k_results=2)
                wiki_tool = WikipediaQueryRun(api_wrapper=wiki_api)
                wiki = wiki_tool.run(course)
                data += f"\n=== Wikipedia ===\n{str(wiki)[:800]}\n"
            except Exception as e:
                print(f"Wikipedia error: {e}")

            prompt = f"""Create comprehensive educational content for {course}.

Research data:
{data}

Include:
1. Course outline with 6-8 major modules
2. Key concepts with clear explanations
3. 4 practical projects (beginner to advanced)
4. Learning resources and next steps

Keep under 4000 words, practical and actionable."""

            response = gemini_llm.call(prompt)

            if hasattr(response, 'content'):
                return str(response.content)[:6000]
            return str(response)[:6000]

        except Exception as e:
            error_msg = f"Error during content creation: {str(e)[:300]}"
            print(error_msg)
            return error_msg


class IntelligentQuizCreator(BaseTool):
    name: str = "Intelligent Assessment Creator"
    description: str = "Generates detailed quizzes with analytics. Input: course name as string."
    args_schema: Type[BaseModel] = CourseInput

    def _run(self, course: str) -> str:
        """Create quiz questions"""
        try:
            # Validate input
            if not course or not isinstance(course, str):
                return "Error: Invalid course name provided"

            course = course.strip()
            print(f"❓ Creating quiz for: {course}")

            search_tool = TavilySearch(topic="general", max_results=3)
            data = ""

            for q in [f"{course} interview questions", f"{course} assessment"]:
                try:
                    time.sleep(0.5)
                    search_result = search_tool.invoke({'query': q})
                    data += f"\n=== {q} ===\n{str(search_result)[:500]}\n"
                except Exception as e:
                    print(f"Search error: {e}")
                    continue

            prompt = f"""Create 30 advanced quiz questions for {course}.

Reference data:
{data}

Requirements:
- 10 beginner questions (foundational concepts)
- 10 intermediate questions (practical application)
- 10 advanced questions (expert-level scenarios)
- Multiple choice format (4 options: A, B, C, D)
- Mark correct answer clearly
- Provide detailed explanation for each answer

Keep under 4000 words total."""

            response = gemini_llm.call(prompt)

            if hasattr(response, 'content'):
                return str(response.content)[:6000]
            return str(response)[:6000]

        except Exception as e:
            error_msg = f"Error creating quiz: {str(e)[:300]}"
            print(error_msg)
            return error_msg


# Initialize tools
Skill_tool = AdvancedSkillDiscovery()
Notes_tool = MultisourceContentCreator()
Quiz_tool = IntelligentQuizCreator()

# Agents with simplified configuration
curriculum_creator_agent = Agent(
    role="Curriculum Designer",
    goal="""Design a world-class, industry-aligned curriculum for {course} that bridges the gap between 
        academic learning and professional requirements. Create a comprehensive skill roadmap that prepares 
        learners for immediate career impact while building long-term expertise.""",
    backstory="""You are a renowned curriculum designer with 15+ years of experience creating educational 
    programs for top-tier universities and Fortune 500 companies. You have personally trained over 10,000 
    professionals and have deep insights into what separates successful learners from the rest.

    Your specialty is creating learning paths that are:
    - Immediately practical and job-relevant
    - Progressive and skill-building
    - Aligned with current industry demands
    - Adaptable to different learning styles
    - Measurable in terms of career outcomes

    You stay current with industry trends by regularly consulting with hiring managers, senior practitioners, 
    and analyzing job market data. Your curricula have a 95% job placement rate within 6 months of completion.""",
    tools=[Skill_tool],
    memory=False,  # Disabled to prevent context overflow
    allow_delegation=False,  # Simplified to prevent errors
    llm=gemini_llm,
    verbose=True
)

content_writer = Agent(
    role="Master Educational Content Strategist & Technical Writer",
    goal="""Create exceptional educational content for {course} that combines theoretical depth with 
    practical application. Transform complex concepts into engaging, memorable learning experiences 
    that stick with students long after they complete the course.""",
    backstory="""You are a master educator and technical writer who has authored 12 bestselling technical 
    books and created content for leading educational platforms like Coursera, Udemy, and Khan Academy. 
    Your content has been viewed by over 2 million learners worldwide.

    Your unique approach combines:
    - Deep technical expertise across multiple domains
    - Exceptional ability to explain complex concepts simply
    - Real-world experience from working in industry
    - Understanding of different learning styles and preferences
    - Mastery of adult learning principles and cognitive science

    You're known for creating content that is:
    - Immediately applicable to real-world problems
    - Rich with practical examples and case studies
    - Structured for optimal knowledge retention
    - Engaging and maintains learner interest
    - Progressive in complexity while remaining accessible

    Your students consistently achieve higher job placement rates and salary increases compared to 
    traditional educational programs.""",
    tools=[Notes_tool],
    memory=False,
    allow_delegation=False,
    llm=gemini_llm,
    verbose=True
)

quiz_maker = Agent(
    role="Senior Learning Assessment Specialist & Educational Psychologist",
    goal="""Design sophisticated, multi-dimensional assessments for {course} that not only test knowledge 
    but also identify learning gaps, measure practical application ability, and provide personalized 
    learning recommendations. Create assessments that serve as both evaluation tools and learning 
    experiences themselves.""",
    backstory="""You are a leading educational psychologist and assessment specialist with a Ph.D. in 
    Cognitive Psychology and 20+ years of experience designing high-stakes assessments for professional 
    certifications, university programs, and corporate training initiatives.

    Your assessment philosophy is built on:
    - Evidence-based measurement of competency
    - Adaptive difficulty that challenges without overwhelming
    - Diagnostic capabilities that identify specific knowledge gaps
    - Real-world scenario-based questions that test application
    - Multi-modal assessment approaches (analytical, practical, creative)

    Your assessments are used by:
    - Top-tier universities for admission and placement
    - Fortune 500 companies for hiring and promotion decisions
    - Professional certification bodies for credentialing
    - Government agencies for skill validation

    You pioneered the "Learning-Through-Assessment" methodology where each question is designed to 
    teach something new while measuring existing knowledge. Your assessments have a 0.97 reliability 
    coefficient and are validated across diverse populations.""",
    tools=[Quiz_tool],
    memory=False,
    allow_delegation=False,
    llm=gemini_llm,
    verbose=True
)

# Tasks
skill_research_task = Task(
    description="""Conduct a comprehensive, market-aligned skills analysis for {course}.

Your analysis must include:

🔍 COMPREHENSIVE SKILL MAPPING
1. Foundation Skills: Core concepts every beginner must master
2. Professional Skills: Job-ready competencies for entry-level positions  
3. Advanced Skills: Senior-level expertise and specialization areas
4. Future Skills: Emerging competencies for career longevity

📊 MARKET INTELLIGENCE 
1. Current Demand: Job posting analysis and hiring trends
2. Salary Benchmarks: Compensation by skill level and geography
3. Growth Projections: 3-5 year outlook for the field
4. Skill Gaps: Where supply doesn't meet demand

🎯 LEARNING PATHWAY DESIGN
1. Prerequisite Analysis: What learners need before starting
2. Skill Dependencies: Which skills build upon others
3. Time-to-Competency: Realistic learning timelines
4. Milestone Markers: How to measure progress

🏆 CERTIFICATION & VALIDATION
1. Industry Certifications: Most valuable credentials to pursue
2. Portfolio Requirements: What projects demonstrate competency
3. Interview Preparation: Technical skills commonly tested
4. Continuous Learning: How to stay current post-completion

Use the Advanced Skill Discovery Tool to gather current market data.""",

    expected_output="""A comprehensive skills analysis document containing:
1. Executive Summary (2-3 paragraphs)
2. Detailed Skills Taxonomy (Foundation → Professional → Advanced → Future)
3. Market Analysis with data and trends
4. Learning Pathway Recommendations
5. Certification and Validation Framework
6. Career Progression Opportunities
7. Next Steps for Curriculum Development

The output should be detailed enough to guide the creation of a professional-grade curriculum.""",

    tools=[Skill_tool],
    agent=curriculum_creator_agent
)

content_task = Task(
    description="""Create exceptional, comprehensive educational content for {course} that transforms learners from 
    beginners to job-ready professionals.

CONTENT CREATION REQUIREMENTS:

📚 COMPREHENSIVE COVERAGE
1. Conceptual Foundation: Core principles explained with real-world analogies
2. Technical Implementation: Step-by-step guides with code examples
3. Practical Projects: 4-6 progressive projects from basic to portfolio-worthy
4. Industry Context: Current best practices and emerging trends
5. Troubleshooting Guide: Common issues and debugging strategies

🎯 LEARNING EXPERIENCE DESIGN
1. Multiple Learning Modalities: Visual, auditory, kinesthetic approaches
2. Progressive Complexity: Each section builds naturally on previous knowledge
3. Immediate Application: Every concept followed by hands-on practice
4. Real-World Relevance: Examples from actual industry scenarios
5. Engagement Elements: Stories, case studies, and memorable examples

🏗️ PRACTICAL PROJECT PORTFOLIO

Project 1 - Foundation Builder (Week 1-2)
- Basic implementation showcasing core concepts
- Clear learning objectives and success criteria
- Extension challenges for advanced learners

Project 2 - Skill Integrator (Week 3-4)
- Combines multiple concepts in realistic scenario
- Includes decision-making and problem-solving
- Introduces industry tools and workflows

Project 3 - Professional Application (Week 5-6)
- Industry-standard complexity and requirements
- Performance optimization and best practices
- Testing, documentation, and deployment

Project 4 - Portfolio Capstone (Week 7-8)
- Showcase-worthy project for job applications
- End-to-end development lifecycle
- Presentation and communication components

Use the Advanced Educational Content Creator tool to gather examples and resources.""",

    expected_output="""A comprehensive educational content package including:

1. Complete Course Content (8-10 major modules)
   - Detailed explanations with examples
   - Progressive skill-building exercises
   - Integration checkpoints and reviews

2. Practical Project Portfolio (4 complete projects)
   - Project specifications and requirements
   - Step-by-step implementation guides
   - Extension challenges and variations

3. Career Preparation Materials
   - Interview question bank with answers
   - Portfolio presentation templates
   - Industry networking strategies

4. Resource Library
   - Curated reading lists and references
   - Tool recommendations and comparisons
   - Community and learning platforms

The content should be immediately usable for self-study or instructor-led training.""",

    tools=[Notes_tool],
    agent=content_writer,
    context=[skill_research_task]
)

quiz_task = Task(
    description="""Design a sophisticated, multi-dimensional assessment system for {course}.

ASSESSMENT DESIGN REQUIREMENTS:

🎯 COMPREHENSIVE EVALUATION FRAMEWORK
1. Knowledge Assessment: Understanding of core concepts and principles
2. Application Testing: Ability to apply concepts to new situations  
3. Analysis Challenges: Problem-solving and critical thinking skills
4. Synthesis Projects: Creating solutions and combining multiple concepts
5. Evaluation Scenarios: Judging quality and making professional decisions

📊 MULTI-LEVEL DIFFICULTY PROGRESSION

Foundation Level (Questions 1-10) - Bloom's Level 1-2
- Core concept recognition and understanding
- Basic terminology and definitions
- Simple application of fundamental principles
- Success Rate Target: 80-90% for course completers

Professional Level (Questions 11-20) - Bloom's Level 3-4
- Real-world scenario problem-solving
- Tool selection and methodology decisions
- Integration of multiple concepts
- Success Rate Target: 70-80% for job-ready learners

Expert Level (Questions 21-30) - Bloom's Level 5-6
- Complex system design and architecture
- Performance optimization and trade-off analysis
- Leadership and strategic decision-making
- Success Rate Target: 60-70% for senior practitioners

🧠 ADVANCED QUESTION DESIGN
- Scenario-Based Questions (40% of assessment)
- Multi-Select Questions (25% of assessment)
- Analytical Questions (25% of assessment)
- Strategic Questions (10% of assessment)

📈 INTELLIGENT FEEDBACK SYSTEM
- Detailed Answer Explanations
- Performance Analytics
- Adaptive Learning Recommendations

Use the Intelligent Assessment Creator tool to gather sample questions and industry standards.""",

    expected_output="""A comprehensive assessment package containing:

1. Primary Assessment (30 questions)
   - 10 Foundation + 10 Professional + 10 Expert level
   - Multiple question types with realistic scenarios
   - Progressive difficulty and comprehensive coverage

2. Complete Answer Key with Explanations
   - Detailed rationale for each correct answer
   - Analysis of why other options are incorrect
   - Learning points and concept reinforcement
   - References to specific content areas

3. Performance Analysis Framework
   - Scoring rubric and interpretation guide
   - Skill gap identification methodology
   - Benchmark data and comparison metrics
   - Career readiness assessment criteria

4. Personalized Learning Recommendations
   - Adaptive feedback based on performance patterns
   - Specific improvement strategies for each skill area
   - Next-step learning pathway suggestions
   - Advanced challenge options for high performers

The assessment should serve as a capstone evaluation that learners can use to 
validate their readiness for professional roles in {course}.""",

    tools=[Quiz_tool],
    agent=quiz_maker,
    context=[content_task]
)

# FastAPI App
app = FastAPI(
    title="AI Curriculum Generator API",
    description="Generate curriculum, content, and quizzes using Gemini + CrewAI",
    version="2.0"
)


class CourseRequest(BaseModel):
    course: str

    class Config:
        title = "CourseRequestModel"


@app.get("/")
async def root():
    return {"message": "✅ AI Curriculum Backend is running successfully!"}


@app.post("/generate/course")
async def generate_course(request: CourseRequest):
    try:
        print(f"\n{'=' * 60}")
        print(f"🚀 Starting course generation for: {request.course}")
        print(f"{'=' * 60}\n")

        crew = Crew(
            agents=[curriculum_creator_agent, content_writer, quiz_maker],
            tasks=[skill_research_task, content_task, quiz_task],
            verbose=True,
            process="sequential"
        )

        result = crew.kickoff(inputs={"course": request.course})

        # Initialize response structure
        response_data = {
            "course": request.course,
            "generated_at": datetime.now().isoformat(),
            "skills_analysis": "",
            "content": "",
            "quiz": ""
        }

        # Extract individual task outputs if available
        if hasattr(result, "tasks_output") and result.tasks_output:
            print(f"\n✅ Processing {len(result.tasks_output)} task outputs\n")

            for i, task_output in enumerate(result.tasks_output):
                output_text = ""

                # Extract text from task output
                if hasattr(task_output, "raw"):
                    output_text = task_output.raw
                elif hasattr(task_output, "output"):
                    output_text = str(task_output.output)
                elif hasattr(task_output, "result"):
                    output_text = str(task_output.result)
                else:
                    output_text = str(task_output)

                # Map to appropriate response field
                if i == 0:  # skill_research_task
                    response_data["skills_analysis"] = output_text
                    print(f"✓ Skills Analysis: {len(output_text)} characters")
                elif i == 1:  # content_task
                    response_data["content"] = output_text
                    print(f"✓ Content: {len(output_text)} characters")
                elif i == 2:  # quiz_task
                    response_data["quiz"] = output_text
                    print(f"✓ Quiz: {len(output_text)} characters")
        else:
            # Fallback: return single output
            if hasattr(result, "raw"):
                response_data["content"] = result.raw
            elif hasattr(result, "output"):
                response_data["content"] = str(result.output)
            else:
                response_data["content"] = str(result)

        print(f"\n{'=' * 60}")
        print("✅ Course generation completed successfully!")
        print(f"{'=' * 60}\n")

        return response_data

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"\n{'=' * 60}")
        print(f"❌ ERROR OCCURRED:")
        print(f"{'=' * 60}")
        print(error_trace)
        print(f"{'=' * 60}\n")

        raise HTTPException(
            status_code=500,
            detail=f"Error generating course: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)