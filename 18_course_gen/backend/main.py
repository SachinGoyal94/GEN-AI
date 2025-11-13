import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from crewai import LLM, Agent, Task, Crew
from datetime import datetime
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
class AdvancedSkillDiscovery(BaseTool):
    name: str = "Advanced Skill Discovery Tool"
    description: str = "Comprehensive skill analysis with industry trends and certifications"

    def _run(self, course: str) -> str:
        try:
            search_tool = TavilySearch(topic="general", max_results=10)
            queries = [
                f"{course} essential skills 2024 industry requirements",
                f"{course} career path roadmap certification",
                f"{course} job market demand salary trends",
                f"{course} latest tools technologies frameworks",
                f"{course} expert skills advanced competencies",
                f"{course} bootcamp curriculum university courses"
            ]

            results = ""
            for q in queries:
                try:
                    results += f"\n=== {q} ===\n{search_tool.invoke({'query': q})}\n"
                except Exception as e:
                    print("Search error:", e)
                    continue

            analysis_prompt = f"""
                You are a senior career advisor and industry expert specializing in {course}.
                Based on the comprehensive research data below, create a detailed skills analysis:
                {results}

                Structure your analysis as follows:

                🎯 **SKILL CATEGORIES & BREAKDOWN**

                **1. FOUNDATIONAL SKILLS (Must-Have)**
                - Core concepts every beginner needs
                - Basic tools and technologies
                - Fundamental principles

                **2. INTERMEDIATE SKILLS (Career Building)**
                - Advanced concepts for job readiness
                - Popular frameworks and tools
                - Problem-solving abilities

                **3. ADVANCED/EXPERT SKILLS (Specialization)**
                - Cutting-edge technologies
                - Leadership and architecture skills
                - Innovation and research abilities

                **4. SOFT SKILLS & COMPLEMENTARY ABILITIES**
                - Communication and collaboration
                - Project management
                - Business understanding

                📊 **MARKET ANALYSIS**
                - Current job market demand
                - Salary expectations by skill level
                - Geographic opportunities
                - Industry growth trends

                🏆 **CERTIFICATION & LEARNING PATHS**
                - Recommended certifications
                - Best learning resources
                - Timeline expectations
                - Career progression milestones

                🔮 **FUTURE TRENDS & EMERGING SKILLS**
                - Technologies to watch
                - Skills that will be obsolete
                - Future-proofing strategies

                Make this comprehensive, actionable, and based on current market realities.
                """
            return gemini_llm.call(analysis_prompt).strip()
        except Exception as e:
            return f"Error during skill discovery: {e}"


class MultisourceContentCreator(BaseTool):
    name: str = "Advanced Educational Content Creator"
    description: str = "Creates comprehensive learning content with examples from web and Wikipedia"

    def _run(self, course: str) -> str:
        try:
            search_tool = TavilySearch(topic="general", max_results=10)
            data = ""
            for q in [f"{course} tutorial", f"{course} projects", f"{course} advanced guide"]:
                try:
                    data += f"\n=== {q} ===\n{search_tool.invoke({'query': q})}\n"
                except:
                    continue

            try:
                wiki_api = WikipediaAPIWrapper(top_k_results=3)
                wiki_tool = WikipediaQueryRun(api_wrapper=wiki_api)
                wiki = wiki_tool.run(course)
                data += f"\n=== Wikipedia ===\n{wiki}\n"
            except:
                pass

            prompt = f"Create a comprehensive educational course for {course} using:\n{data}"
            return gemini_llm.call(prompt)
        except Exception as e:
            return f"Error during content creation: {e}"

class IntelligentQuizCreator(BaseTool):
    name: str = "Intelligent Assessment Creator"
    description: str = "Generates detailed quizzes with analytics"

    def _run(self, course: str) -> str:
        try:
            search_tool = TavilySearch(topic="general", max_results=5)
            data = ""
            for q in [f"{course} interview questions", f"{course} assessment"]:
                data += f"\n=== {q} ===\n{search_tool.invoke({'query': q})}\n"
            prompt = f"Create 30 advanced quiz questions for {course} with explanations using:\n{data}"
            return gemini_llm.call(prompt)
        except Exception as e:
            return f"Error creating quiz: {e}"
Skill_tool = AdvancedSkillDiscovery()
Notes_tool = MultisourceContentCreator()
Quiz_tool = IntelligentQuizCreator()

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
    memory=True,
    allow_delegation=True,
    llm=gemini_llm,
    system_message="""When designing curricula, always consider:
    1. Current market demand and salary potential
    2. Prerequisite skills and knowledge gaps
    3. Hands-on project integration
    4. Industry certification alignment
    5. Career progression pathways
    6. Measurable learning outcomes
    7. Time-to-competency optimization

    Structure your analysis to show clear skill progression from beginner to expert level.
    Include specific tools, technologies, and methodologies currently used in the industry.
    Provide realistic timelines and learning milestones."""
)

content_writer = Agent(
    role="Master Educational Content Strategist & Technical Writer",
    goal="""Create exceptional educational content for {course} that combines theoretical depth with 
    practical application. Transform complex concepts into engaging, memorable learning experiences 
    that stick with students long after they complete the course.""",

    verbose=True,
    memory=True,

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
    allow_delegation=True,
    llm=gemini_llm,

    system_message="""When creating educational content, follow these principles:
    1. Start with clear learning objectives and outcomes
    2. Use the 'show, explain, practice' methodology
    3. Include multiple real-world examples and case studies
    4. Provide hands-on exercises that build upon each other
    5. Address common misconceptions and pitfalls explicitly
    6. Include troubleshooting guides and debugging tips
    7. Connect each topic to career applications and value
    8. Use analogies and mental models for complex concepts
    9. Provide multiple difficulty levels and extension challenges
    10. Include assessment checkpoints throughout the content

    Make every section actionable - learners should be able to immediately apply what they've learned."""
)

quiz_maker = Agent(
    role="Senior Learning Assessment Specialist & Educational Psychologist",
    goal="""Design sophisticated, multi-dimensional assessments for {course} that not only test knowledge 
    but also identify learning gaps, measure practical application ability, and provide personalized 
    learning recommendations. Create assessments that serve as both evaluation tools and learning 
    experiences themselves.""",

    verbose=True,
    memory=True,

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
    coefficient and are validated across diverse populations.

    Your specialties include:
    - Bloom's Taxonomy application for progressive difficulty
    - Item Response Theory for optimal question selection
    - Bias detection and mitigation in assessment design
    - Performance prediction and career readiness measurement""",

    tools=[Quiz_tool],
    allow_delegation=False,
    llm=gemini_llm,

    system_message="""When creating assessments, apply these advanced principles:

    ASSESSMENT DESIGN:
    1. Map questions to specific learning objectives
    2. Use progressive difficulty (Bloom's Taxonomy levels)
    3. Include scenario-based questions that test application
    4. Create plausible distractors based on common misconceptions
    5. Ensure questions test understanding, not just memorization
    6. Include questions that require synthesis and analysis
    7. Design for diagnostic capability (identify specific gaps)

    QUESTION QUALITY:
    1. Each question should have ONE clearly best answer
    2. Incorrect options should be educationally valuable
    3. Use current, industry-relevant examples and scenarios
    4. Avoid trick questions or ambiguous wording
    5. Include visual/practical elements where appropriate
    6. Test practical application, not just theoretical knowledge

    LEARNING ANALYTICS:
    1. Provide detailed explanations that teach
    2. Include learning recommendations for missed questions
    3. Map performance to skill areas for gap analysis
    4. Offer next-step learning suggestions
    5. Provide benchmark data for self-assessment

    Create assessments that learners want to retake because they learn something new each time."""
)



skill_research_task = Task(
    description="""
    Conduct a comprehensive, market-aligned skills analysis for {course} that serves as the foundation 
    for world-class curriculum design.

    Your analysis must include:

    🔍 **COMPREHENSIVE SKILL MAPPING**
    1. **Foundation Skills**: Core concepts every beginner must master
    2. **Professional Skills**: Job-ready competencies for entry-level positions  
    3. **Advanced Skills**: Senior-level expertise and specialization areas
    4. **Future Skills**: Emerging competencies for career longevity

    📊 **MARKET INTELLIGENCE** 
    1. **Current Demand**: Job posting analysis and hiring trends
    2. **Salary Benchmarks**: Compensation by skill level and geography
    3. **Growth Projections**: 3-5 year outlook for the field
    4. **Skill Gaps**: Where supply doesn't meet demand

    🎯 **LEARNING PATHWAY DESIGN**
    1. **Prerequisite Analysis**: What learners need before starting
    2. **Skill Dependencies**: Which skills build upon others
    3. **Time-to-Competency**: Realistic learning timelines
    4. **Milestone Markers**: How to measure progress

    🏆 **CERTIFICATION & VALIDATION**
    1. **Industry Certifications**: Most valuable credentials to pursue
    2. **Portfolio Requirements**: What projects demonstrate competency
    3. **Interview Preparation**: Technical skills commonly tested
    4. **Continuous Learning**: How to stay current post-completion

    **DELIVERABLE FORMAT:**
    - Executive summary with key insights
    - Detailed skill breakdown by proficiency level
    - Visual learning pathway/roadmap
    - Market data with sources and methodology
    - Actionable recommendations for curriculum design

    **QUALITY STANDARDS:**
    - Base recommendations on current job market data (2024)
    - Include specific tool/technology names and versions
    - Provide quantitative metrics where possible (salary ranges, job counts)
    - Reference authoritative industry sources
    - Consider different career paths within the field
    """,

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
    description="""
    Create exceptional, comprehensive educational content for {course} that transforms learners from 
    beginners to job-ready professionals. This content will serve as the definitive learning resource.

    **CONTENT CREATION REQUIREMENTS:**

    📚 **COMPREHENSIVE COVERAGE**
    1. **Conceptual Foundation**: Core principles explained with real-world analogies
    2. **Technical Implementation**: Step-by-step guides with code examples
    3. **Practical Projects**: 4-6 progressive projects from basic to portfolio-worthy
    4. **Industry Context**: Current best practices and emerging trends
    5. **Troubleshooting Guide**: Common issues and debugging strategies

    🎯 **LEARNING EXPERIENCE DESIGN**
    1. **Multiple Learning Modalities**: Visual, auditory, kinesthetic approaches
    2. **Progressive Complexity**: Each section builds naturally on previous knowledge
    3. **Immediate Application**: Every concept followed by hands-on practice
    4. **Real-World Relevance**: Examples from actual industry scenarios
    5. **Engagement Elements**: Stories, case studies, and memorable examples

    🏗️ **PRACTICAL PROJECT PORTFOLIO**

    **Project 1 - Foundation Builder** (Week 1-2)
    - Basic implementation showcasing core concepts
    - Clear learning objectives and success criteria
    - Extension challenges for advanced learners

    **Project 2 - Skill Integrator** (Week 3-4)  
    - Combines multiple concepts in realistic scenario
    - Includes decision-making and problem-solving
    - Introduces industry tools and workflows

    **Project 3 - Professional Application** (Week 5-6)
    - Industry-standard complexity and requirements
    - Performance optimization and best practices
    - Testing, documentation, and deployment

    **Project 4 - Portfolio Capstone** (Week 7-8)
    - Showcase-worthy project for job applications
    - End-to-end development lifecycle
    - Presentation and communication components

    💼 **CAREER PREPARATION INTEGRATION**
    1. **Interview Preparation**: Technical questions and portfolio presentation
    2. **Industry Insights**: Day-in-the-life scenarios and career paths
    3. **Networking Guidance**: Communities, conferences, and professional development
    4. **Salary Negotiation**: Market rates and value proposition building

    🔬 **ADVANCED TOPICS & SPECIALIZATIONS**
    1. **Emerging Technologies**: What's coming next in the field
    2. **Specialization Paths**: Different career trajectories and focuses
    3. **Research Opportunities**: Academic and industry research directions
    4. **Leadership Development**: Technical leadership and mentoring skills

    **CONTENT STRUCTURE REQUIREMENTS:**
    - Each major section: Learning objectives → Theory → Practice → Assessment
    - Code examples with line-by-line explanations
    - Visual aids: diagrams, flowcharts, screenshots
    - "Pro Tips" boxes with expert insights
    - "Common Pitfalls" warnings with solutions
    - "Real-World Application" case studies
    - "Further Reading" resources for deep dives

    **QUALITY STANDARDS:**
    - Content should support 60-80 hours of comprehensive study
    - Include at least 20 practical exercises/mini-projects
    - Reference current industry tools and practices (2024)
    - Provide multiple solution approaches where applicable
    - Include performance benchmarks and optimization tips
    - Ensure content is accessible to diverse learning backgrounds
    """,

    expected_output="""A comprehensive educational content package including:

    1. **Complete Course Content** (8-10 major modules)
       - Detailed explanations with examples
       - Progressive skill-building exercises
       - Integration checkpoints and reviews

    2. **Practical Project Portfolio** (4 complete projects)
       - Project specifications and requirements
       - Step-by-step implementation guides
       - Extension challenges and variations

    3. **Career Preparation Materials**
       - Interview question bank with answers
       - Portfolio presentation templates
       - Industry networking strategies

    4. **Resource Library**
       - Curated reading lists and references
       - Tool recommendations and comparisons
       - Community and learning platforms

    The content should be immediately usable for self-study or instructor-led training, 
    with clear learning paths for different experience levels.""",

    tools=[Notes_tool],
    agent=content_writer,
    context=[skill_research_task]
)

quiz_task = Task(
    description="""
    Design a sophisticated, multi-dimensional assessment system for {course} that serves as both 
    evaluation and learning tool. Create an assessment that accurately measures competency while 
    providing detailed feedback for improvement.

    **ASSESSMENT DESIGN REQUIREMENTS:**

    🎯 **COMPREHENSIVE EVALUATION FRAMEWORK**
    1. **Knowledge Assessment**: Understanding of core concepts and principles
    2. **Application Testing**: Ability to apply concepts to new situations  
    3. **Analysis Challenges**: Problem-solving and critical thinking skills
    4. **Synthesis Projects**: Creating solutions and combining multiple concepts
    5. **Evaluation Scenarios**: Judging quality and making professional decisions

    📊 **MULTI-LEVEL DIFFICULTY PROGRESSION**

    **Foundation Level (Questions 1-10)** - Bloom's Level 1-2
    - Core concept recognition and understanding
    - Basic terminology and definitions
    - Simple application of fundamental principles
    - Success Rate Target: 80-90% for course completers

    **Professional Level (Questions 11-20)** - Bloom's Level 3-4
    - Real-world scenario problem-solving
    - Tool selection and methodology decisions
    - Integration of multiple concepts
    - Success Rate Target: 70-80% for job-ready learners

    **Expert Level (Questions 21-30)** - Bloom's Level 5-6
    - Complex system design and architecture
    - Performance optimization and trade-off analysis
    - Leadership and strategic decision-making
    - Success Rate Target: 60-70% for senior practitioners

    🧠 **ADVANCED QUESTION DESIGN**

    **Scenario-Based Questions (40% of assessment)**
    - Present realistic workplace challenges
    - Require application of multiple concepts
    - Include sufficient context and constraints
    - Test practical decision-making abilities

    **Multi-Select Questions (25% of assessment)**
    - Test comprehensive understanding
    - Identify partial knowledge gaps
    - Require careful consideration of all options
    - Prevent lucky guessing on complex topics

    **Analytical Questions (25% of assessment)**
    - Present code/data/scenarios for analysis
    - Test debugging and troubleshooting skills
    - Require identification of issues and solutions
    - Mirror real-world problem-solving tasks

    **Strategic Questions (10% of assessment)**
    - Focus on high-level decision making
    - Test understanding of business context
    - Evaluate leadership and communication skills
    - Assess career-readiness for senior roles

    📈 **INTELLIGENT FEEDBACK SYSTEM**

    **Detailed Answer Explanations**
    - Why each correct answer is the best choice
    - Common misconceptions behind incorrect options
    - Additional context and learning opportunities
    - References to specific content sections for review

    **Performance Analytics**
    - Skill area breakdown and gap identification
    - Comparison to benchmark performance data
    - Personalized improvement recommendations
    - Next-step learning pathway suggestions

    **Adaptive Learning Recommendations**
    - Specific content areas to review based on performance
    - Supplementary resources for weak areas
    - Advanced topics for high performers
    - Career readiness assessment and guidance

    **QUESTION QUALITY STANDARDS:**
    - Each question tests a specific, important concept
    - Incorrect options represent realistic misconceptions
    - Language is clear, unambiguous, and professional
    - Questions reflect current industry practices (2024)
    - Scenarios use realistic data and constraints
    - All options are plausible to someone with partial knowledge
    - Questions avoid cultural bias and accessibility issues

    **ASSESSMENT VALIDATION:**
    - Map each question to specific learning objectives
    - Ensure progressive difficulty within each level
    - Validate with industry experts and practitioners
    - Test for reliability and consistency
    - Analyze for potential bias or unfairness
    """,

    expected_output="""A comprehensive assessment package containing:

    1. **Primary Assessment** (30 questions)
       - 10 Foundation + 10 Professional + 10 Expert level
       - Multiple question types with realistic scenarios
       - Progressive difficulty and comprehensive coverage

    2. **Complete Answer Key with Explanations**
       - Detailed rationale for each correct answer
       - Analysis of why other options are incorrect
       - Learning points and concept reinforcement
       - References to specific content areas

    3. **Performance Analysis Framework**
       - Scoring rubric and interpretation guide
       - Skill gap identification methodology
       - Benchmark data and comparison metrics
       - Career readiness assessment criteria

    4. **Personalized Learning Recommendations**
       - Adaptive feedback based on performance patterns
       - Specific improvement strategies for each skill area
       - Next-step learning pathway suggestions
       - Advanced challenge options for high performers

    5. **Assessment Analytics**
       - Question difficulty and discrimination analysis
       - Learning objective coverage mapping
       - Performance prediction indicators
       - Continuous improvement recommendations

    The assessment should serve as a capstone evaluation that learners can use to 
    validate their readiness for professional roles in {course}.""",

    tools=[Quiz_tool],
    agent=quiz_maker,
    context=[content_task]
)


app = FastAPI(
    title="AI Curriculum Generator API",
    description="Generate curriculum, content, and quizzes using Gemini + CrewAI",
    version="1.0"
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
        crew = Crew(
            agents=[curriculum_creator_agent, content_writer, quiz_maker],
            tasks=[skill_research_task, content_task, quiz_task],
            verbose=True,
            process="sequential"  # ✅ Tasks run in order with context
        )

        result = crew.kickoff(inputs={"course": request.course})

        # Initialize response structure
        response_data = {
            "course": request.course,
            "skills_analysis": "",
            "content": "",
            "quiz": ""
        }

        # Extract individual task outputs if available
        if hasattr(result, "tasks_output") and result.tasks_output:
            for i, task_output in enumerate(result.tasks_output):
                output_text = ""

                # Extract text from task output
                if hasattr(task_output, "raw"):
                    output_text = task_output.raw
                elif hasattr(task_output, "output"):
                    output_text = str(task_output.output)

                # Map to appropriate response field
                if i == 0:  # skill_research_task
                    response_data["skills_analysis"] = output_text
                elif i == 1:  # content_task
                    response_data["content"] = output_text
                elif i == 2:  # quiz_task
                    response_data["quiz"] = output_text
        else:
            # Fallback: return single output
            if hasattr(result, "raw"):
                response_data["content"] = result.raw
            elif hasattr(result, "output"):
                response_data["content"] = str(result.output)

        return response_data

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Error generating course: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT",10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
