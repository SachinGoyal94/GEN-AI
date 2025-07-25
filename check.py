import os
import re
import gradio as gr
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import BaseTool

# Load .env variables
load_dotenv()

# Define a dummy YouTube search tool
class YoutubeChannelSearchTool(BaseTool):
    name: str = "YouTube Channel Search Tool"
    description: str = (
        "Fetches video information from a YouTube channel handle. "
        "Returns a string summary of recent videos or search results."
    )

    def _run(self, youtube_channel_handle: str) -> str:
        return (
            f"Simulated data for channel '{youtube_channel_handle}':\n"
            f"Video 1: 'Understanding AI vs ML vs DL' - This video provides a foundational "
            f"understanding of Artificial Intelligence, Machine Learning, and Deep Learning, "
            f"highlighting their differences and interconnections.\n\n"
            f"Video 2: 'Latest Trends in Generative AI' - Discusses recent advancements and "
            f"future prospects in generative AI.\n\n"
            f"Video 3: 'Practical Machine Learning with Python' - A tutorial-style video "
            f"demonstrating ML using Python libraries."
        )

yt_tool = YoutubeChannelSearchTool()

# Load Gemini API key
gemini_key = os.getenv("GEMINI_KEY")
if not gemini_key:
    raise ValueError("❌ GEMINI_KEY not found. Please set it in your .env file.")

# Initialize LLM
gemini_llm = LLM(
    model='gemini-2.5-flash-lite-preview-06-17',
    api_key=gemini_key
)

# Define agents
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

# Define tasks
def create_tasks(topic):
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
    return [research_task, write_task]

# Main function for Gradio
def generate_blog(channel_handle, topic):
    if not channel_handle or not topic:
        return "❗Please enter both YouTube channel handle and blog topic.", None

    try:
        tasks = create_tasks(topic)

        crew = Crew(
            agents=[blog_researcher, blog_writer],
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )

        result = crew.kickoff(inputs={'topic': topic, 'youtube_channel_handle': channel_handle})
        clean_filename = re.sub(r'[\\/:*?"<>|]', '', topic)
        file_path = f"/tmp/{clean_filename}_blog_post.md"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(result)

        return result, file_path

    except Exception as e:
        return f"⚠️ Error: {str(e)}", None

# Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("## ✍️ YouTube Blog Creator with CrewAI + Gemini")
    gr.Markdown("Enter a YouTube channel handle and a blog topic to generate an AI-powered blog post.")

    with gr.Row():
        yt_input = gr.Textbox(label="YouTube Channel Handle", placeholder="@krishnaik06")
        topic_input = gr.Textbox(label="Blog Topic", placeholder="AI vs ML vs DL")

    gen_btn = gr.Button("Generate Blog Post")
    output_blog = gr.Textbox(label="Generated Blog", lines=15)
    download = gr.File(label="Download Blog", file_types=[".md"])

    def run_and_display(channel, topic):
        result, path = generate_blog(channel, topic)
        return result, path

    gen_btn.click(fn=run_and_display, inputs=[yt_input, topic_input], outputs=[output_blog, download])

# Run the Gradio app
if __name__ == "__main__":
    demo.launch()
