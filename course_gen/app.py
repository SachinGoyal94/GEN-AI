import streamlit as st
import time
import os
import sys
from datetime import datetime
import threading
import queue
import io
from contextlib import redirect_stdout, redirect_stderr

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# CrewAI imports
try:
    from crewai import Crew, Process
    from tasks import skill_research_task, content_research_task, Quiz_creator_task
    from curriculum_agent import curriculum_creator_agent, content_writer, quiz_maker
    from llm import gemini_llm
    from tools import Skill_tool, WikiPedia_tool, Notes_tool, Quiz_tool

    CREWAI_AVAILABLE = True
except ImportError as e:
    CREWAI_AVAILABLE = False
    IMPORT_ERROR = str(e)

# Configure page
st.set_page_config(
    page_title="🚀 Cosmic Learning Hub",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'generation_complete' not in st.session_state:
    st.session_state.generation_complete = False
if 'generated_content' not in st.session_state:
    st.session_state.generated_content = ""
if 'generated_quiz' not in st.session_state:
    st.session_state.generated_quiz = ""
if 'generation_logs' not in st.session_state:
    st.session_state.generation_logs = ""
if 'current_course' not in st.session_state:
    st.session_state.current_course = ""


# Custom CSS for space theme
def load_custom_css():
    st.markdown("""
    <style>
    /* Import fonts */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Exo+2:wght@300;400;600&display=swap');

    /* Main app styling */
    .stApp {
        background: linear-gradient(135deg, #0c0c1d 0%, #1a1a2e 25%, #16213e 50%, #0f3460 100%);
        color: #e0e6ed;
    }

    /* Headers */
    .main-header {
        font-family: 'Orbitron', monospace;
        font-size: 3.5rem;
        font-weight: 900;
        text-align: center;
        background: linear-gradient(45deg, #64b5f6, #42a5f5, #2196f3, #1976d2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 2rem;
        text-shadow: 0 0 20px rgba(33, 150, 243, 0.5);
    }

    .section-header {
        font-family: 'Orbitron', monospace;
        font-size: 1.8rem;
        color: #64b5f6;
        margin: 2rem 0 1rem 0;
        text-shadow: 0 0 10px rgba(100, 181, 246, 0.3);
    }

    /* Cards and containers */
    .cosmic-card {
        background: linear-gradient(135deg, rgba(26, 26, 46, 0.8), rgba(22, 33, 62, 0.6));
        border: 1px solid rgba(100, 181, 246, 0.3);
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), 0 0 20px rgba(100, 181, 246, 0.1);
        backdrop-filter: blur(10px);
    }

    .mission-control {
        background: linear-gradient(135deg, rgba(15, 52, 96, 0.8), rgba(22, 33, 62, 0.6));
        border: 2px solid rgba(100, 181, 246, 0.4);
        border-radius: 20px;
        padding: 2rem;
        margin: 2rem 0;
        position: relative;
        overflow: hidden;
    }

    .mission-control::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(100, 181, 246, 0.1), transparent);
        transition: left 0.5s;
    }

    .mission-control:hover::before {
        left: 100%;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #2196f3, #1976d2);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.8rem 2rem;
        font-family: 'Exo 2', sans-serif;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(33, 150, 243, 0.4);
    }

    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(33, 150, 243, 0.6);
    }

    /* Input fields */
    .stTextInput > div > div > input {
        background: rgba(26, 26, 46, 0.8);
        border: 2px solid rgba(100, 181, 246, 0.3);
        border-radius: 10px;
        color: #e0e6ed;
        padding: 0.8rem;
        font-family: 'Exo 2', sans-serif;
    }

    .stTextInput > div > div > input:focus {
        border-color: #64b5f6;
        box-shadow: 0 0 20px rgba(100, 181, 246, 0.3);
    }

    /* Select boxes */
    .stSelectbox > div > div > select {
        background: rgba(26, 26, 46, 0.8);
        color: #e0e6ed;
        border: 2px solid rgba(100, 181, 246, 0.3);
        border-radius: 10px;
    }

    /* Progress bars */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #64b5f6, #2196f3);
    }

    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #0c0c1d 0%, #1a1a2e 100%);
    }

    /* Content styling */
    .generated-content {
        background: rgba(15, 52, 96, 0.4);
        border-left: 4px solid #64b5f6;
        padding: 1.5rem;
        border-radius: 10px;
        font-family: 'Exo 2', sans-serif;
        line-height: 1.6;
        max-height: 500px;
        overflow-y: auto;
    }

    .logs-container {
        background: rgba(12, 12, 29, 0.8);
        border: 1px solid rgba(100, 181, 246, 0.2);
        border-radius: 10px;
        padding: 1rem;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        color: #90a4ae;
        max-height: 300px;
        overflow-y: auto;
    }

    /* Metrics */
    .metric-container {
        background: linear-gradient(135deg, rgba(100, 181, 246, 0.1), rgba(33, 150, 243, 0.1));
        border-radius: 15px;
        padding: 1rem;
        text-align: center;
        border: 1px solid rgba(100, 181, 246, 0.2);
    }

    /* Status indicators */
    .status-ready {
        color: #4caf50;
        font-weight: bold;
    }

    .status-generating {
        color: #ff9800;
        font-weight: bold;
        animation: pulse 2s infinite;
    }

    .status-complete {
        color: #64b5f6;
        font-weight: bold;
    }

    .status-error {
        color: #f44336;
        font-weight: bold;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    /* Stars animation */
    .stars {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: -1;
    }

    .star {
        position: absolute;
        width: 2px;
        height: 2px;
        background: #ffffff;
        border-radius: 50%;
        animation: twinkle 3s infinite;
    }

    @keyframes twinkle {
        0%, 100% { opacity: 0.3; }
        50% { opacity: 1; }
    }

    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }

    .floating {
        animation: float 3s ease-in-out infinite;
    }

    </style>
    """, unsafe_allow_html=True)


def create_stars_background():
    """Create animated starfield background"""
    stars_html = """
    <div class="stars">
    """ + "".join(
        [f'<div class="star" style="left: {i * 3.7}%; top: {i * 7.3 % 100}%; animation-delay: {i * 0.1}s;"></div>' for i
         in range(100)]) + """
    </div>
    """
    st.markdown(stars_html, unsafe_allow_html=True)


def run_crew_generation(course_name, progress_callback=None, log_callback=None):
    """Run the CrewAI generation process"""
    try:
        if not CREWAI_AVAILABLE:
            return None, None, f"CrewAI not available: {IMPORT_ERROR}"

        # Capture stdout and stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr

        # Create string buffers
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        # Redirect outputs
        sys.stdout = stdout_buffer
        sys.stderr = stderr_buffer

        try:
            # Create the crew
            crew = Crew(
                agents=[curriculum_creator_agent, content_writer, quiz_maker],
                tasks=[skill_research_task, content_research_task, Quiz_creator_task],
                process=Process.sequential,
                verbose=True,
            )

            # Update progress
            if progress_callback:
                progress_callback(25, "🚀 Crew assembled, starting generation...")

            # Run the crew
            result = crew.kickoff(inputs={'course': course_name})

            if progress_callback:
                progress_callback(75, "📝 Processing outputs...")

            # Get outputs
            try:
                content_output = str(content_research_task.output.raw) if hasattr(content_research_task.output,
                                                                                  'raw') else str(
                    content_research_task.output)
                quiz_output = str(Quiz_creator_task.output.raw) if hasattr(Quiz_creator_task.output, 'raw') else str(
                    Quiz_creator_task.output)
            except:
                content_output = "Content generation completed - check logs for details"
                quiz_output = "Quiz generation completed - check logs for details"

            # Get logs
            logs = stdout_buffer.getvalue() + stderr_buffer.getvalue()

            if progress_callback:
                progress_callback(100, "✅ Generation complete!")

            return content_output, quiz_output, logs

        finally:
            # Restore stdout and stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    except Exception as e:
        return None, None, f"Error during generation: {str(e)}"


def show_generation_progress(course_name):
    """Show real-time generation progress"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    logs_container = st.empty()

    # Progress tracking
    progress_value = 0
    status_message = "🛰️ Initializing mission parameters..."

    def update_progress(value, message):
        nonlocal progress_value, status_message
        progress_value = value
        status_message = message
        progress_bar.progress(value)
        status_text.markdown(f"<div class='status-generating'>{message}</div>", unsafe_allow_html=True)

    def update_logs(log_message):
        if log_message:
            logs_container.markdown(f"<div class='logs-container'>{log_message}</div>", unsafe_allow_html=True)

    # Run generation in thread
    update_progress(10, "🔍 Analyzing course requirements...")
    time.sleep(1)

    update_progress(20, "🤖 Initializing AI agents...")
    time.sleep(1)

    # Run actual crew generation
    content_output, quiz_output, logs = run_crew_generation(course_name, update_progress, update_logs)

    # Update logs
    if logs:
        update_logs(logs)

    # Complete
    progress_bar.progress(100)
    status_text.markdown("<div class='status-complete'>🎉 Mission accomplished!</div>", unsafe_allow_html=True)

    return content_output, quiz_output, logs


def save_generated_files(course_name, content, quiz):
    """Save generated content to files"""
    try:
        # Create data directory if it doesn't exist
        os.makedirs("data/generated", exist_ok=True)

        base = course_name.replace(' ', '_').lower()

        # Save individual files
        content_file = f"data/generated/{base}_content.txt"
        quiz_file = f"data/generated/{base}_quiz.txt"
        complete_file = f"data/generated/{base}_complete.txt"

        with open(content_file, 'w', encoding='utf-8') as f:
            f.write(content)

        with open(quiz_file, 'w', encoding='utf-8') as f:
            f.write(quiz)

        # Combined file
        combined = f"""=== CONTENT ===

{content}

=== QUIZ ===

{quiz}
"""

        with open(complete_file, 'w', encoding='utf-8') as f:
            f.write(combined)

        return content_file, quiz_file, complete_file

    except Exception as e:
        st.error(f"Error saving files: {str(e)}")
        return None, None, None


def main():
    load_custom_css()
    create_stars_background()

    # Main header
    st.markdown("<h1 class='main-header floating'>🌌 COSMIC LEARNING HUB 🚀</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center; font-size: 1.2rem; color: #90a4ae; font-family: Exo 2;'>AI-Powered Educational Content Generation with CrewAI</p>",
        unsafe_allow_html=True)

    # Check CrewAI availability
    if not CREWAI_AVAILABLE:
        st.error(f"⚠️ CrewAI components not available: {IMPORT_ERROR}")
        st.info(
            "Please ensure all required modules (crewai, tasks, curriculum_agent, llm, tools) are properly installed and configured.")
        return

    # Sidebar - Mission Control
    with st.sidebar:
        st.markdown("<div class='section-header'>🎯 Mission Control</div>", unsafe_allow_html=True)

        # Course selection
        course_input = st.text_input(
            "🎓 Enter Course/Topic",
            value=st.session_state.get('last_course', ''),
            placeholder="e.g., Machine Learning, Web Development, Data Science",
            help="Enter any topic you want to create educational content for"
        )

        # Content type selection
        content_type = st.selectbox(
            "📚 Generation Mode",
            ["Complete Course Package", "Content Focus", "Assessment Focus"],
            help="Choose what type of content to prioritize"
        )

        # Advanced options
        with st.expander("🔧 Advanced Settings"):
            verbose_mode = st.checkbox("Verbose Logging", value=True, help="Show detailed generation logs")
            auto_save = st.checkbox("Auto-save Files", value=True, help="Automatically save generated content to files")

        # Generate button
        generate_btn = st.button("🚀 Launch Generation Mission", type="primary", use_container_width=True)

        # Clear button
        if st.button("🧹 Clear Mission Data", use_container_width=True):
            st.session_state.generation_complete = False
            st.session_state.generated_content = ""
            st.session_state.generated_quiz = ""
            st.session_state.generation_logs = ""
            st.session_state.current_course = ""
            st.rerun()

        # Mission stats
        st.markdown("<div class='section-header'>📊 System Status</div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            status = "🟢 READY" if CREWAI_AVAILABLE else "🔴 ERROR"
            st.markdown(f"<div class='metric-container'><h4>System</h4><p>{status}</p></div>", unsafe_allow_html=True)
        with col2:
            agents_status = "3 Active" if CREWAI_AVAILABLE else "0 Active"
            st.markdown(f"<div class='metric-container'><h4>Agents</h4><p>{agents_status}</p></div>",
                        unsafe_allow_html=True)

    # Main content area
    if generate_btn and course_input:
        st.session_state.current_course = course_input
        st.session_state.last_course = course_input

        st.markdown(f"<div class='section-header'>🎯 Mission: {course_input}</div>", unsafe_allow_html=True)

        # Mission briefing
        with st.container():
            st.markdown(f"""
            <div class='mission-control'>
                <h3>🛰️ Mission Briefing</h3>
                <p><strong>Target Course:</strong> {course_input}</p>
                <p><strong>Generation Mode:</strong> {content_type}</p>
                <p><strong>AI Agents:</strong> Curriculum Designer, Content Creator, Quiz Maker</p>
                <p><strong>Status:</strong> <span class='status-generating'>🚀 Launching...</span></p>
            </div>
            """, unsafe_allow_html=True)

        # Generation process
        st.markdown("<div class='section-header'>🤖 AI Crew Working...</div>", unsafe_allow_html=True)

        with st.container():
            content_output, quiz_output, logs = show_generation_progress(course_input)

            # Store in session state
            if content_output and quiz_output:
                st.session_state.generated_content = content_output
                st.session_state.generated_quiz = quiz_output
                st.session_state.generation_logs = logs
                st.session_state.generation_complete = True

                # Auto-save files
                if auto_save:
                    content_file, quiz_file, complete_file = save_generated_files(course_input, content_output,
                                                                                  quiz_output)
                    if content_file:
                        st.success(f"✅ Files automatically saved: {content_file}, {quiz_file}, {complete_file}")
            else:
                st.error("❌ Generation failed. Check logs for details.")

    # Display generated content
    if st.session_state.generation_complete and st.session_state.generated_content:
        course_name = st.session_state.current_course

        st.markdown("<div class='section-header'>📚 Generated Educational Content</div>", unsafe_allow_html=True)

        # Content tabs
        tab1, tab2, tab3 = st.tabs(["📖 Course Content", "🧠 Assessment Quiz", "🔍 Generation Logs"])

        with tab1:
            st.markdown("<h4>🎓 Comprehensive Course Material</h4>", unsafe_allow_html=True)
            content_container = st.container()
            with content_container:
                st.markdown(f"<div class='generated-content'><pre>{st.session_state.generated_content}</pre></div>",
                            unsafe_allow_html=True)

            # Download content
            st.download_button(
                "📄 Download Course Content",
                st.session_state.generated_content,
                f"{course_name.replace(' ', '_').lower()}_content.txt",
                "text/plain",
                key="download_content"
            )

        with tab2:
            st.markdown("<h4>🧪 Knowledge Assessment Quiz</h4>", unsafe_allow_html=True)
            quiz_container = st.container()
            with quiz_container:
                st.markdown(f"<div class='generated-content'><pre>{st.session_state.generated_quiz}</pre></div>",
                            unsafe_allow_html=True)

            # Download quiz
            st.download_button(
                "🧠 Download Quiz",
                st.session_state.generated_quiz,
                f"{course_name.replace(' ', '_').lower()}_quiz.txt",
                "text/plain",
                key="download_quiz"
            )

        with tab3:
            st.markdown("<h4>🔍 AI Generation Process Logs</h4>", unsafe_allow_html=True)
            if st.session_state.generation_logs:
                st.markdown(f"<div class='logs-container'><pre>{st.session_state.generation_logs}</pre></div>",
                            unsafe_allow_html=True)
            else:
                st.info("No detailed logs available for this generation session.")

        # Combined download
        st.markdown("---")
        combined_content = f"""=== COURSE CONTENT ===

{st.session_state.generated_content}

=== ASSESSMENT QUIZ ===

{st.session_state.generated_quiz}

=== GENERATION LOGS ===

{st.session_state.generation_logs}
"""

        col1, col2, col3 = st.columns(3)
        with col2:
            st.download_button(
                "📦 Download Complete Package",
                combined_content,
                f"{course_name.replace(' ', '_').lower()}_complete_package.txt",
                "text/plain",
                key="download_complete",
                use_container_width=True
            )

        # Mission complete status
        st.markdown(f"""
        <div class='mission-control'>
            <h3>🎉 Mission Complete!</h3>
            <p><strong>Course:</strong> {course_name}</p>
            <p><strong>Status:</strong> <span class='status-complete'>✅ Successfully Generated</span></p>
            <p><strong>Components:</strong> Curriculum ✓ | Content ✓ | Assessment ✓</p>
            <p>Your educational package is ready for deployment! 🚀</p>
        </div>
        """, unsafe_allow_html=True)

    elif not st.session_state.generation_complete:
        # Welcome screen
        st.markdown("""
        <div class='cosmic-card'>
            <h2>🌟 Welcome to the Cosmic Learning Hub</h2>
            <p>Transform any topic into a comprehensive educational experience using CrewAI-powered multi-agent systems.</p>

            <h3>🚀 AI Agent Team</h3>
            <ul>
                <li><strong>🎓 Curriculum Designer:</strong> Creates structured learning pathways and skill breakdowns</li>
                <li><strong>📚 Content Creator:</strong> Generates comprehensive educational material with examples</li>
                <li><strong>🧠 Quiz Maker:</strong> Develops multi-level assessments to test knowledge retention</li>
            </ul>

            <h3>🎯 How It Works</h3>
            <ol>
                <li>Enter your desired course or topic in Mission Control</li>
                <li>Configure generation settings and preferences</li>
                <li>Launch the AI crew to create your content</li>
                <li>Review, download, and deploy your educational package</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

        # Feature showcase
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            <div class='cosmic-card'>
                <h3>🤖 Multi-Agent AI</h3>
                <p>Specialized agents work together to create comprehensive educational content.</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class='cosmic-card'>
                <h3>📊 Real-time Processing</h3>
                <p>Watch your content being generated with live progress tracking and logs.</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown("""
            <div class='cosmic-card'>
                <h3>🌐 Advanced Research</h3>
                <p>AI agents use web search and knowledge synthesis for rich, current content.</p>
            </div>
            """, unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div style='margin-top: 4rem; text-align: center; color: #546e7a; font-family: Exo 2;'>
        <p>🌌 Powered by CrewAI & Cosmic Intelligence • Built for Educators & Learners</p>
        <p>✨ "Education is the most powerful weapon which you can use to change the world." - Nelson Mandela</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()