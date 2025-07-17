#from crewai_tools import YoutubeChannelSearchTool
#yt_tool = YoutubeChannelSearchTool(youtube_channel_handle='@krishnaik06')
#the above code is not working so  creating a custom tool

from crewai.tools import BaseTool

# Custom tool to fetch YouTube channel data
class YoutubeChannelSearchTool(BaseTool):
    name: str = "YouTube Channel Search Tool"
    description: str = (
        "Fetches video information from a YouTube channel handle. "
        "Returns a string summary of recent videos or search results."
    )

    def _run(self, youtube_channel_handle: str) -> str:
        # Simulate video data (replace with real API call if needed)
        print(f"--- Searching YouTube for channel: {youtube_channel_handle} ---")
        return (
            f"Sample data for channel {youtube_channel_handle}:\n"
            "- 'AI vs ML vs DL Explained' — 250K views, uploaded 3 days ago\n"
            "- 'LangChain Tutorial for Beginners' — 180K views, uploaded 1 week ago\n"
            "- 'Prompt Engineering Tips' — 150K views, uploaded 2 weeks ago\n"
            "- Consistent posting on AI/ML/GenAI topics, mostly 10–15 min videos.\n"
            "- Engagement is high, with frequent Q&A in comments."
        )

yt_tool = YoutubeChannelSearchTool()
