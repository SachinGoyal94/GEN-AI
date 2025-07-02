from fastapi import FastAPI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
from pydantic import BaseModel
import uvicorn
load_dotenv()

gemini_api_key = os.getenv("GEMINI_KEY")
model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", api_key=gemini_api_key)

generic_template = "translate the following into {language}:"
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", generic_template),
        ("user", "{text}")
    ]
)

parser = StrOutputParser()

chain = prompt | model | parser


# --- API Schema Definition ---
# Define the input schema for your chain using Pydantic.
# This will be used to validate the request body in our custom endpoint.
class TranslationRequest(BaseModel):
    language: str
    text: str


# --- FastAPI Application ---
# Define the main application
app = FastAPI(
    title="LangChain Translator Server",
    version="1.0",
    description="A simple API server using LangChain to translate text."
)

# --- Custom API Endpoint ---
# Instead of using add_routes, we define a standard FastAPI POST endpoint.
# This gives us more control and avoids potential issues with langserve's automatic schema generation.
@app.post("/translate")
async def translate(request: TranslationRequest):
    """
    Translates the given text into the specified language.
    """
    # Create the input dictionary for the chain from the request body
    input_data = {"language": request.language, "text": request.text}

    # Invoke the LangChain chain with the input data
    # We use ainvoke for asynchronous execution, which is best practice in FastAPI
    result = await chain.ainvoke(input_data)

    # Return the result
    return {"translation": result}


# --- Main Entry Point ---
# This block allows you to run the server directly from the script
if __name__ == "__main__":
    # Running with reload=True is helpful for development as it restarts the server on code changes.
    uvicorn.run(app, host="127.0.0.1", port=8000)
