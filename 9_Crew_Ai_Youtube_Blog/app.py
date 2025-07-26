import gradio as gr
import os
from dotenv import load_dotenv
import re

load_dotenv()

from crewai.tools import BaseTool


class YoutubeChannelSearchTool(BaseTool):
    name: str = "YouTube Channel Search Tool"
    description: str = (
        "Fetches video information from a YouTube channel handle. "
        "Returns a string summary of recent videos or search results."
    )

    def _run(self, youtube_channel_handle: str) -> str:
        # This is a simulated function. In a real scenario, you'd integrate
        # with the YouTube Data API to fetch actual video transcripts/info.
        print(f"--- Simulating search for YouTube channel: {youtube_channel_handle} ---")
        # For demonstration, returning a generic message.
        # In a real app, this would involve API calls to get video data.
        return (
            f"Simulated data for channel '{youtube_channel_handle}':\n"
        )


yt_tool = YoutubeChannelSearchTool()

from crewai import LLM

gemini_key = os.getenv("GEMINI_KEY")

if not gemini_key:
    raise ValueError("GEMINI_KEY not found. Please set it in your environment variables.")

try:
    gemini_llm = LLM(
        model='gemini/gemini-2.5-pro',  # Or 'gemini-1.5-flash' for faster responses
        api_key=gemini_key
    )
except Exception as e:
    raise Exception(f"Failed to initialize LLM. Check your API key and model name: {e}")

from crewai import Agent

blog_researcher = Agent(
    role="Blog Researcher from youtube videos",
    goal="get the relevant video transcription for the topic {topic} from the provided Youtube Channel",
    verbose=True,
    memory=True,
    backstory="AI Data Science and Gen AI Expert in understanding Youtube videos",
    tools=[yt_tool],
    allow_delegation=True,
    llm=gemini_llm
)

blog_writer = Agent(
    role="Blog writer",
    goal="Narrate compelling tech stories from yt video {topic} from Youtube",
    verbose=True,
    memory=True,
    backstory=(
        "With a flair for simplifying complex topics, you craft "
        "engaging narratives that captivate and educate, bringing new "
        "discoveries to light in an accessible manner."
    ),
    tools=[yt_tool],
    allow_delegation=False,
    llm=gemini_llm
)

from crewai import Task

research_task = Task(
    description=(
        "Identify the video related to '{topic}' from the provided YouTube channel handle."
        "Get detailed information about the video content, focusing on key concepts and explanations."
    ),
    expected_output='A comprehensive 3 paragraphs long report based on the {topic} of video content.',
    tools=[yt_tool],
    agent=blog_researcher
)

write_task = Task(
    description=(
        "Using the information gathered by the researcher on the topic '{topic}' from the YouTube video, "
        "summarize the key points and create a compelling blog post. "
        "The blog post should be well-structured, engaging, and easy to understand for a general audience."
    ),
    expected_output='A well-structured and engaging blog post about {topic} based on the YouTube video content.',
    tools=[yt_tool],
    agent=blog_writer,
    async_execution=False,
)


def generate_blog_post(youtube_channel_handle, blog_topic):
    """
    Generate blog post based on YouTube channel and topic
    """
    if not youtube_channel_handle or not blog_topic:
        return "❌ **Error**: Please enter both the YouTube Channel Handle and the Blog Topic.", None

    try:
        from crewai import Crew, Process
        crew = Crew(
            agents=[blog_researcher, blog_writer],
            tasks=[research_task, write_task],
            process=Process.sequential,
            verbose=True,
        )

        result = crew.kickoff(inputs={'topic': blog_topic, 'youtube_channel_handle': youtube_channel_handle})

        # Create downloadable file content
        safe_filename = re.sub(r'[\\/:*?"<>|]', '', blog_topic)
        file_content = str(result)

        return str(result), file_content

    except Exception as e:
        return f"❌ **An error occurred**: {e}", None


# Custom CSS for stunning eye-catching design
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

.gradio-container {
    background: linear-gradient(135deg, #0c0c1e 0%, #1a0033 25%, #0f172a 50%, #1e1b4b 75%, #0c0c1e 100%);
    background-size: 400% 400%;
    animation: gradientShift 15s ease infinite;
    min-height: 100vh;
    font-family: 'Inter', sans-serif;
}

@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

#header {
    text-align: center;
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(59, 130, 246, 0.2) 50%, rgba(16, 185, 129, 0.1) 100%);
    backdrop-filter: blur(25px);
    border: 2px solid rgba(139, 92, 246, 0.3);
    color: white;
    padding: 4rem 2rem;
    border-radius: 25px;
    margin-bottom: 3rem;
    box-shadow: 
        0 20px 60px rgba(139, 92, 246, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.1);
    position: relative;
    overflow: hidden;
}

#header::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
    animation: shimmer 3s infinite;
}

@keyframes shimmer {
    0% { left: -100%; }
    100% { left: 100%; }
}

#header h1 {
    font-size: 4rem;
    margin-bottom: 1rem;
    font-weight: 800;
    background: linear-gradient(135deg, #a855f7, #3b82f6, #10b981, #f59e0b);
    background-size: 300% 300%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: textGradient 4s ease infinite;
    text-shadow: 0 0 30px rgba(168, 85, 247, 0.5);
}

@keyframes textGradient {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

#header p {
    font-size: 1.4rem;
    margin: 0;
    font-weight: 400;
    color: #e2e8f0;
    text-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
}

.input-container {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(51, 65, 85, 0.8) 100%);
    backdrop-filter: blur(25px);
    padding: 3rem;
    border-radius: 25px;
    box-shadow: 
        0 25px 50px rgba(0, 0, 0, 0.4),
        0 0 0 1px rgba(139, 92, 246, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.1);
    margin-bottom: 2rem;
    border: 1px solid rgba(139, 92, 246, 0.3);
    position: relative;
    overflow: hidden;
}

.input-container::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.8), transparent);
}

.output-container {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(51, 65, 85, 0.8) 100%);
    backdrop-filter: blur(25px);
    padding: 3rem;
    border-radius: 25px;
    box-shadow: 
        0 25px 50px rgba(0, 0, 0, 0.4),
        0 0 0 1px rgba(139, 92, 246, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(139, 92, 246, 0.3);
    position: relative;
    overflow: hidden;
}

.output-container::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.8), transparent);
}

.section-title {
    color: #a855f7;
    font-weight: 700;
    font-size: 1.6rem;
    margin-bottom: 2rem;
    text-shadow: 0 0 20px rgba(168, 85, 247, 0.4);
    position: relative;
}

.section-title::after {
    content: '';
    position: absolute;
    bottom: -5px;
    left: 0;
    width: 60px;
    height: 3px;
    background: linear-gradient(90deg, #a855f7, #3b82f6);
    border-radius: 2px;
}

.generate-btn {
    background: linear-gradient(135deg, #9333ea 0%, #3b82f6 100%) !important;
    border: none !important;
    padding: 1.2rem 4rem !important;
    font-size: 1.3rem !important;
    font-weight: 700 !important;
    border-radius: 20px !important;
    box-shadow: 
        0 10px 30px rgba(147, 51, 234, 0.5),
        0 0 0 1px rgba(147, 51, 234, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    color: white !important;
    text-transform: uppercase;
    letter-spacing: 1px;
    position: relative;
    overflow: hidden;
}

.generate-btn::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    transition: left 0.5s;
}

.generate-btn:hover::before {
    left: 100%;
}

.generate-btn:hover {
    transform: translateY(-5px) scale(1.02) !important;
    box-shadow: 
        0 20px 40px rgba(147, 51, 234, 0.6),
        0 0 0 1px rgba(147, 51, 234, 0.5),
        inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
    background: linear-gradient(135deg, #7c3aed 0%, #2563eb 100%) !important;
}

.generate-btn:active {
    transform: translateY(-2px) scale(0.98) !important;
}

.status-box {
    padding: 2rem;
    border-radius: 20px;
    margin: 2rem 0;
    font-weight: 600;
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    position: relative;
    overflow: hidden;
}

.status-box::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    opacity: 0.8;
}

.status-success {
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(16, 185, 129, 0.3));
    color: #6ee7b7;
    border-color: rgba(34, 197, 94, 0.4);
    box-shadow: 0 10px 25px rgba(34, 197, 94, 0.2);
}

.status-success::before {
    background: linear-gradient(90deg, #10b981, #34d399);
}

.status-error {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(220, 38, 38, 0.3));
    color: #fca5a5;
    border-color: rgba(239, 68, 68, 0.4);
    box-shadow: 0 10px 25px rgba(239, 68, 68, 0.2);
}

.status-error::before {
    background: linear-gradient(90deg, #ef4444, #f87171);
}

.status-working {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(217, 119, 6, 0.3));
    color: #fcd34d;
    border-color: rgba(245, 158, 11, 0.4);
    box-shadow: 0 10px 25px rgba(245, 158, 11, 0.2);
}

.status-working::before {
    background: linear-gradient(90deg, #f59e0b, #fbbf24);
}

.feature-card {
    background: linear-gradient(135deg, rgba(51, 65, 85, 0.8) 0%, rgba(71, 85, 105, 0.6) 100%);
    backdrop-filter: blur(25px);
    padding: 2.5rem;
    border-radius: 20px;
    box-shadow: 
        0 15px 35px rgba(0, 0, 0, 0.3),
        0 0 0 1px rgba(139, 92, 246, 0.2);
    border: 1px solid rgba(139, 92, 246, 0.2);
    margin: 2rem 0;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    position: relative;
    overflow: hidden;
}

.feature-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.8), transparent);
    opacity: 0;
    transition: opacity 0.3s;
}

.feature-card:hover {
    transform: translateY(-8px) scale(1.02);
    box-shadow: 
        0 25px 50px rgba(139, 92, 246, 0.3),
        0 0 0 1px rgba(139, 92, 246, 0.4);
    border-color: rgba(139, 92, 246, 0.5);
}

.feature-card:hover::before {
    opacity: 1;
}

.feature-card h3 {
    color: #c4b5fd;
    margin-bottom: 1rem;
    font-size: 1.4rem;
    font-weight: 600;
    text-shadow: 0 0 15px rgba(196, 181, 253, 0.3);
}

.feature-card p {
    color: #cbd5e1;
    line-height: 1.7;
    font-weight: 400;
}

.download-section {
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(16, 185, 129, 0.3));
    backdrop-filter: blur(20px);
    color: #6ee7b7;
    padding: 2.5rem;
    border-radius: 20px;
    margin-top: 2rem;
    box-shadow: 0 15px 35px rgba(34, 197, 94, 0.3);
    border: 1px solid rgba(34, 197, 94, 0.4);
    position: relative;
    overflow: hidden;
}

.download-section::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, #10b981, #34d399);
}

/* Enhanced input styling */
.gr-textbox input {
    background: linear-gradient(135deg, rgba(51, 65, 85, 0.9) 0%, rgba(71, 85, 105, 0.8) 100%) !important;
    border: 2px solid rgba(139, 92, 246, 0.3) !important;
    border-radius: 15px !important;
    padding: 1rem 1.5rem !important;
    font-size: 1.1rem !important;
    color: #e2e8f0 !important;
    font-weight: 500 !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 
        0 4px 15px rgba(0, 0, 0, 0.2),
        inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
}

.gr-textbox input:focus {
    border-color: #a855f7 !important;
    box-shadow: 
        0 0 0 4px rgba(168, 85, 247, 0.2),
        0 8px 25px rgba(139, 92, 246, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
    background: linear-gradient(135deg, rgba(51, 65, 85, 1) 0%, rgba(71, 85, 105, 0.9) 100%) !important;
    transform: translateY(-2px);
}

.gr-textbox input::placeholder {
    color: #94a3b8 !important;
    font-weight: 400;
}

.gr-textbox label {
    color: #c4b5fd !important;
    font-weight: 600 !important;
    font-size: 1.1rem !important;
    margin-bottom: 0.8rem !important;
    text-shadow: 0 0 10px rgba(196, 181, 253, 0.3);
}

/* Enhanced markdown styling */
.gr-markdown {
    color: #e2e8f0 !important;
    line-height: 1.8;
}

.gr-markdown h1, .gr-markdown h2, .gr-markdown h3 {
    color: #c4b5fd !important;
    text-shadow: 0 0 15px rgba(196, 181, 253, 0.3);
}

.gr-markdown p {
    color: #cbd5e1 !important;
    line-height: 1.7;
}

.gr-markdown strong {
    color: #a855f7 !important;
}

/* Better spacing and layout */
.gr-group {
    gap: 2rem;
}

.gr-column {
    gap: 2rem;
}

/* Custom scrollbar */
::-webkit-scrollbar {
    width: 10px;
}

::-webkit-scrollbar-track {
    background: rgba(30, 41, 59, 0.5);
    border-radius: 5px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #9333ea, #3b82f6);
    border-radius: 5px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #7c3aed, #2563eb);
}

/* Glow effects for interactivity */
.interactive-glow {
    position: relative;
}

.interactive-glow::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border-radius: inherit;
    padding: 2px;
    background: linear-gradient(135deg, #9333ea, #3b82f6, #10b981);
    mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    mask-composite: exclude;
    opacity: 0;
    transition: opacity 0.3s;
}

.interactive-glow:hover::after {
    opacity: 0.6;
}
"""

# Create Gradio interface with dark theme
theme = gr.themes.Soft(
    primary_hue="violet",
    secondary_hue="blue",
    neutral_hue="slate"
).set(
    body_background_fill="linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%)",
    background_fill_primary="rgba(30, 41, 59, 0.8)",
    background_fill_secondary="rgba(51, 65, 85, 0.6)",
    border_color_primary="rgba(147, 51, 234, 0.3)",
    button_primary_background_fill="linear-gradient(135deg, #9333ea 0%, #3b82f6 100%)",
    button_primary_background_fill_hover="linear-gradient(135deg, #7c3aed 0%, #2563eb 100%)",
    button_primary_text_color="white",
    input_background_fill="rgba(51, 65, 85, 0.8)",
    input_border_color="rgba(147, 51, 234, 0.4)"
).set(
    body_background_fill="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    background_fill_primary="rgba(255, 255, 255, 0.95)",
    background_fill_secondary="rgba(255, 255, 255, 0.9)",
    border_color_primary="#e5e7eb",
    button_primary_background_fill="linear-gradient(135deg, #7c3aed 0%, #a855f7 100%)",
    button_primary_background_fill_hover="linear-gradient(135deg, #6d28d9 0%, #9333ea 100%)",
    button_primary_text_color="white",
    button_primary_border_color="transparent",
    input_background_fill="white",
    input_border_color="#d1d5db",
    input_border_width="2px"
)

with gr.Blocks(
        title="YouTube Blog Post Creator",
        theme=theme,
        css=custom_css
) as demo:
    # Header Section
    with gr.Row(elem_id="header"):
        gr.HTML("""
            <div id="header">
                <h1>✍️ YouTube Blog Post Creator</h1>
                <p>Transform YouTube content into engaging blog posts using AI-powered research and writing</p>
            </div>
        """)

    with gr.Row():
        with gr.Column(scale=1):
            # Input Section
            with gr.Group(elem_classes=["input-container"]):
                gr.Markdown("### 🎯 Configuration", elem_classes=["section-title"])

                with gr.Row():
                    youtube_channel_handle = gr.Textbox(
                        label="📺 YouTube Channel Handle",
                        placeholder="e.g., @krishnaik06, @3Blue1Brown, @sentdex",
                        value="@krishnaik06",
                        info="Enter the YouTube channel handle to research",
                        container=True,
                        scale=2
                    )

                with gr.Row():
                    blog_topic = gr.Textbox(
                        label="📝 Blog Topic",
                        placeholder="e.g., Machine Learning, Neural Networks, Data Science",
                        value="AI vs ML vs DL",
                        info="Specify the topic you want the blog post to cover",
                        container=True,
                        scale=2
                    )

                with gr.Row():
                    generate_btn = gr.Button(
                        "🚀 Generate Blog Post",
                        variant="primary",
                        size="lg",
                        elem_classes=["generate-btn"],
                        scale=1
                    )

                # Status indicator
                status_box = gr.HTML(visible=False)

        with gr.Column(scale=1):
            # Features section
            gr.HTML("""
                <div class="feature-card">
                    <h3>🤖 AI-Powered Research</h3>
                    <p>Our AI agents analyze YouTube content to extract key insights and concepts</p>
                </div>
                <div class="feature-card">
                    <h3>📚 Smart Content Creation</h3>
                    <p>Transform video content into well-structured, engaging blog posts</p>
                </div>
                <div class="feature-card">
                    <h3>⬇️ Instant Download</h3>
                    <p>Get your blog post as a downloadable Markdown file</p>
                </div>
            """)

    # Output Section
    with gr.Row():
        with gr.Column():
            with gr.Group(elem_classes=["output-container"]):
                gr.Markdown("### 📄 Generated Blog Post", elem_classes=["section-title"])

                blog_output = gr.Markdown(
                    value="🎬 **Ready to create amazing content!** \n\nEnter your YouTube channel and topic above, then click 'Generate Blog Post' to get started.",
                    elem_classes=["blog-content"],
                    container=True
                )

                download_section = gr.HTML(visible=False)
                download_file = gr.File(
                    label="📥 Download Your Blog Post",
                    visible=False,
                    elem_classes=["download-file"]
                )


    # Event handlers
    def handle_generation(channel, topic):
        if not channel or not topic:
            status_html = """
                <div class="status-box status-error">
                    ⚠️ Please enter both the YouTube Channel Handle and the Blog Topic.
                </div>
            """
            return (
                "❌ **Missing Information**: Please fill in both fields above to generate your blog post.",
                status_html,
                gr.update(visible=True),
                None,
                gr.update(visible=False),
                gr.update(visible=False)
            )

        # Show working status
        working_status = """
            <div class="status-box status-working">
                🔄 AI crew is researching and writing your blog post... This may take a few moments.
            </div>
        """

        try:
            blog_content, file_content = generate_blog_post(channel, topic)

            if file_content and not blog_content.startswith(("❌", "⚠️")):
                # Success
                safe_filename = re.sub(r'[\\/:*?"<>|]', '', topic)
                temp_file_path = f"{safe_filename}-blog-post.md"

                with open(temp_file_path, 'w', encoding='utf-8') as f:
                    f.write(file_content)

                success_status = """
                    <div class="status-box status-success">
                        ✅ Blog post generated successfully! Your content is ready for download.
                    </div>
                """

                download_html = f"""
                    <div class="download-section">
                        <h4>🎉 Success! Your blog post is ready</h4>
                        <p>Click the download button below to save your blog post as a Markdown file.</p>
                    </div>
                """

                return (
                    blog_content,
                    success_status,
                    gr.update(visible=True),
                    temp_file_path,
                    gr.update(visible=True),
                    download_html
                )
            else:
                # Error
                error_status = """
                    <div class="status-box status-error">
                        ❌ An error occurred while generating the blog post. Please try again.
                    </div>
                """
                return (
                    blog_content,
                    error_status,
                    gr.update(visible=True),
                    None,
                    gr.update(visible=False),
                    gr.update(visible=False)
                )

        except Exception as e:
            error_status = f"""
                <div class="status-box status-error">
                    ❌ Error: {str(e)}
                </div>
            """
            return (
                f"❌ **An error occurred**: {e}",
                error_status,
                gr.update(visible=True),
                None,
                gr.update(visible=False),
                gr.update(visible=False)
            )


    # Show working status when button is clicked
    def show_working_status():
        working_status = """
            <div class="status-box status-working">
                🔄 AI crew is researching and writing your blog post... This may take a few moments.
            </div>
        """
        return working_status, gr.update(visible=True)


    generate_btn.click(
        fn=show_working_status,
        outputs=[status_box, status_box],
        show_progress=False
    ).then(
        fn=handle_generation,
        inputs=[youtube_channel_handle, blog_topic],
        outputs=[blog_output, status_box, status_box, download_file, download_file, download_section],
        show_progress=True
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render uses 10000 by default
    demo.launch(
        server_name="0.0.0.0",   # Required for public access
        server_port=port,        # Port expected by Render
        share=False,
        debug=True,
        inbrowser=False          # Not needed on server
    )
