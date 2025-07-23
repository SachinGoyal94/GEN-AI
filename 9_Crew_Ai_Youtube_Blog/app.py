import streamlit as st
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
        st.info(f"--- Simulating search for YouTube channel: {youtube_channel_handle} ---")
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

gemini_key = os.getenv("GEMINI_KEY") or st.secrets.get("GEMINI_KEY")

if not gemini_key:
    st.error("GEMINI_KEY not found. Please set it in your environment variables or Streamlit secrets.")
    st.stop()

try:
    gemini_llm = LLM(
        model='gemini/gemini-2.5-pro', # Or 'gemini-1.5-flash' for faster responses
        api_key=gemini_key
    )
except Exception as e:
    st.error(f"Failed to initialize LLM. Check your API key and model name: {e}")
    st.stop()


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

st.set_page_config(page_title="YouTube Blog Post Creator", layout="centered")

st.title("✍️ YouTube Blog Post Creator")
st.markdown(
    """
    This app uses CrewAI to research a given topic from a YouTube channel
    and then generate a blog post based on the video content.
    """
)

st.subheader("Configuration")
youtube_channel_handle = st.text_input(
    "Enter YouTube Channel Handle (e.g., @krishnaik06)",
    value="@krishnaik06",
    help="The YouTube channel handle to research (e.g., @GoogleDevelopers)"
)
blog_topic = st.text_input(
    "Enter Blog Topic (e.g., AI vs ML vs DL)",
    value="AI vs ML vs DL",
    help="The specific topic you want the blog post to be about."
)

if st.button("Generate Blog Post"):
    if not youtube_channel_handle or not blog_topic:
        st.warning("Please enter both the YouTube Channel Handle and the Blog Topic.")
    else:
        st.subheader("Generating Blog Post...")
        with st.spinner("Crew is working hard to research and write your blog post..."):
            try:
                from crewai import Crew, Process
                crew = Crew(
                    agents=[blog_researcher, blog_writer],
                    tasks=[research_task, write_task],
                    process=Process.sequential,
                    verbose=True,
                )

                result = crew.kickoff(inputs={'topic': blog_topic, 'youtube_channel_handle': youtube_channel_handle})

                st.success("Blog post generated successfully!")
                st.subheader("Generated Blog Post:")
                st.markdown(result)

                safe_filename = re.sub(r'[\\/:*?"<>|]', '', blog_topic) # Remove invalid characters
                st.download_button(
                    label="Download Blog Post as Markdown",
                    data=str(result), # Explicitly convert CrewOutput to string
                    file_name=f"{safe_filename}-blog-post.md",
                    mime="text/markdown"
                )


            except Exception as e:
                st.error(f"An error occurred: {e}")