import streamlit as st

import langchain_google_genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

import os
from dotenv import load_dotenv
load_dotenv()

## Langsmith Tracking
os.environ["GOOGLE_API_KEY"] =os.getenv("GEMINI_KEY")
os.environ["LANGCHAIN_API_KEY"]=os.getenv("LANGCHAIN_KEY")
os.environ["LANGCHAIN_TRACING_V2"]="true"
os.environ["LANGCHAIN_PROJECT"]="Simple Q&A Chatbot With Gemini"

## Prompt Template
prompt=ChatPromptTemplate.from_messages(
    [
        ("system","You are a helpful assistant . Please  response to the user queries"),
        ("user","Question:{question}")
    ]
)

def generate_response(question,api_key,engine,temperature,max_tokens):
    os.environ["GOOGLE_API_KEY"] = api_key

    llm=ChatGoogleGenerativeAI(model=engine)
    output_parser=StrOutputParser()
    chain=prompt|llm|output_parser
    answer=chain.invoke({'question':question})
    return answer

## #Title of the app
st.title("Enhanced Q&A Chatbot With Gemini")



## Sidebar for settings
st.sidebar.title("Settings")
api_key=st.sidebar.text_input("Enter your Gemini API Key:",type="password")

## Select the OpenAI model
engine=st.sidebar.selectbox("Select Gemini model",["gemini-1.5-flash","gemini-2.0-flash","gemini-2.5-pro"])

## Adjust response parameter
temperature=st.sidebar.slider("Temperature",min_value=0.0,max_value=1.0,value=0.7)
max_tokens = st.sidebar.slider("Max Tokens", min_value=50, max_value=300, value=150)

## MAin interface for user input
st.write("Go ahead and ask any question")
user_input=st.text_input("You:")

if user_input and api_key:
    response=generate_response(user_input,api_key,engine,temperature,max_tokens)
    st.write(response)

elif user_input:
    st.warning("Please enter the Gemini API Key in the sider bar")
else:
    st.write("Please provide the user input")


