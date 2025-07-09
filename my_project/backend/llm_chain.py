import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Please respond carefully."),
    ("user", "Question: {question}")
])

def get_chain(engine):
    llm = ChatGoogleGenerativeAI(model=engine)
    output_parser = StrOutputParser()
    chain = prompt | llm | output_parser
    return chain
