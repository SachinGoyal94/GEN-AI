from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Ensure Ollama server is running and model is pulled before running this.
# If your Ollama server is on a different host/port, specify base_url
# llm = ChatOllama(model="llama2-uncensored", base_url="http://your-ollama-host:11434")
llm = ChatOllama(model="llama2-uncensored")

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("user", "Question: {question}")
])
output_parser = StrOutputParser()
chain = prompt | llm | output_parser

try:
    response = chain.invoke({"question": "What is the capital of France?"})
    print("Ollama Test Success:", response)
except Exception as e:
    print("Ollama Test Failed:", e)