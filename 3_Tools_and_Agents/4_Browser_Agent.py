import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

os.environ["GOOGLE_API_KEY"]=os.getenv("GEMINI_KEY")
from browser_use import Agent,ChatGoogle
async def main():
    agent=Agent(
        task="go to https://www.linkedin.com/in/sachin-goyal-518770311/ and help me to find Sachin Goyal from Ludhiana Punjab studying at Thapar Institute of Engineering and Technology",
        llm=ChatGoogle(model="gemini-2.5-flash-lite")
    )
    await agent.run()
asyncio.run(main())