import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

os.environ["GOOGLE_API_KEY"]=os.getenv("GEMINI_KEY")
from browser_use import Agent,ChatGoogle
async def main():
    agent=Agent(
        task="go to github.com and help me to get a best repo's for agentic ai",
        llm=ChatGoogle(model="gemini-2.5-flash-lite")
    )
    await agent.run()
asyncio.run(main())