from crewai import Task
from curriculum_agent import (
    curriculum_creator_agent,
    content_writer,
    quiz_maker,
    research_analyst_agent,
    quality_assurance_agent
)
from tools import Skill_tool, WikiPedia_tool, Notes_tool, Quiz_tool
from llm import gemini_llm

# Enhanced Skills Research Task with comprehensive analysis
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
    agent=curriculum_creator_agent,
    output_file="skills_analysis.md"
)

# Enhanced Content Research Task with multi-source synthesis
content_research_task = Task(
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

    tools=[Notes_tool, WikiPedia_tool],
    agent=content_writer,
    context=[skill_research_task],
    output_file="course_content.md"
)

# Enhanced Quiz Creation Task with advanced assessment design
Quiz_creator_task = Task(
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
    context=[content_research_task],
    output_file="comprehensive_assessment.md"
)

# Additional Quality Assurance Task
quality_review_task = Task(
    description="""
    Conduct a comprehensive quality review of all generated educational materials for {course} 
    to ensure they meet the highest standards of educational excellence and professional relevance.

    **QUALITY REVIEW FRAMEWORK:**

    📋 **CONTENT ACCURACY & CURRENCY**
    - Verify all technical information is current (2024 standards)
    - Check code examples for syntax and best practices
    - Validate industry references and market data
    - Ensure tool versions and recommendations are up-to-date

    🎯 **LEARNING EFFECTIVENESS**
    - Evaluate logical progression and skill building
    - Assess clarity of explanations and examples
    - Review practical exercises for appropriate difficulty
    - Validate learning objectives alignment

    💼 **PROFESSIONAL RELEVANCE**
    - Confirm content matches current industry needs
    - Verify project portfolios meet hiring standards
    - Assess career preparation materials for accuracy
    - Validate salary and market data

    🔍 **ASSESSMENT QUALITY**
    - Review question clarity and answer accuracy
    - Validate difficulty progression and coverage
    - Check feedback quality and learning value
    - Ensure assessment reliability and fairness

    **IMPROVEMENT RECOMMENDATIONS:**
    Provide specific, actionable suggestions for enhancing content quality,
    learning effectiveness, and professional relevance.
    """,

    expected_output="""A comprehensive quality review report with:
    1. Overall quality score and assessment
    2. Detailed findings by content area
    3. Specific improvement recommendations
    4. Priority actions for maximum impact
    5. Validation of professional standards compliance""",

    tools=[Notes_tool],
    agent=quality_assurance_agent,
    context=[skill_research_task, content_research_task, Quiz_creator_task]
)