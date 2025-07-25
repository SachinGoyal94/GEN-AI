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
            f"Video 1: 'Understanding AI vs ML vs DL' - This video provides a foundational "
            f"understanding of Artificial Intelligence, Machine Learning, and Deep Learning, "
            f"highlighting their differences and interconnections. It covers basic definitions, "
            f"historical context, and practical applications of each field.\n\n"
            f"Video 2: 'Latest Trends in Generative AI' - Discusses recent advancements and "
            f"future prospects in generative AI, including large language models and image generation. "
            f"It delves into the ethical considerations and potential societal impacts.\n\n"
            f"Video 3: 'Practical Machine Learning with Python' - A tutorial-style video "
            f"demonstrating how to implement various machine learning algorithms using Python "
            f"libraries like scikit-learn and TensorFlow. It includes a hands-on example."
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
        return "Error: Please enter both the YouTube Channel Handle and the Blog Topic.", None

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
        return f"An error occurred: {e}", None


# Create Gradio interface
with gr.Blocks(title="YouTube Blog Post Creator", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # ✍️ YouTube Blog Post Creator

        This app uses CrewAI to research a given topic from a YouTube channel
        and then generate a blog post based on the video content.
        """
    )

    with gr.Column():
        gr.Markdown("## Configuration")

        youtube_channel_handle = gr.Textbox(
            label="YouTube Channel Handle",
            placeholder="e.g., @krishnaik06",
            value="@krishnaik06",
            info="The YouTube channel handle to research (e.g., @GoogleDevelopers)"
        )

        blog_topic = gr.Textbox(
            label="Blog Topic",
            placeholder="e.g., AI vs ML vs DL",
            value="AI vs ML vs DL",
            info="The specific topic you want the blog post to be about."
        )

        generate_btn = gr.Button("Generate Blog Post", variant="primary", size="lg")

    with gr.Column():
        gr.Markdown("## Generated Blog Post")

        blog_output = gr.Markdown(
            label="Blog Post Content",
            value="Click 'Generate Blog Post' to create your content..."
        )

        download_file = gr.File(
            label="Download Blog Post",
            visible=False
        )


    # Event handlers
    def handle_generation(channel, topic):
        if not channel or not topic:
            return "⚠️ Please enter both the YouTube Channel Handle and the Blog Topic.", None

        try:
            blog_content, file_content = generate_blog_post(channel, topic)

            if file_content:
                # Create temporary file for download
                safe_filename = re.sub(r'[\\/:*?"<>|]', '', topic)
                temp_file_path = f"{safe_filename}-blog-post.md"

                with open(temp_file_path, 'w', encoding='utf-8') as f:
                    f.write(file_content)

                return blog_content, temp_file_path
            else:
                return blog_content, None

        except Exception as e:
            return f"❌ An error occurred: {e}", None


    generate_btn.click(
        fn=handle_generation,
        inputs=[youtube_channel_handle, blog_topic],
        outputs=[blog_output, download_file]
    )

    # Show download file when content is generated
    blog_output.change(
        fn=lambda x: gr.update(visible=bool(x and not x.startswith(("⚠️", "❌")))),
        inputs=[blog_output],
        outputs=[download_file]
    )
if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",  # Use localhost instead of 0.0.0.0
        server_port=7860,
        share=False,
        debug=True,
        inbrowser=True  # Automatically open browser
    )