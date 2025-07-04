import os
from dotenv import load_dotenv

from langchain_community.llms import ollama
import streamlit as st
from langchain_community.llms.ollama import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

#Langchain Tracing
os.environ["LANGCHAIN_API_KEY"]=os.getenv("LANGCHAIN_KEY")
os.environ["LANGCHAIN_TRACING_V2"]="true"
os.environ["LANGCHAIN_PROJECT"]=os.getenv("LANGCHAIN_PROJECT")

prompt=ChatPromptTemplate.from_messages([
    ("system","you are a helpful assistant,Please Respond Carefully"),
    ("user","Question:{question}")
]
)

#Streamlit Framework
st.title("A helpful assistant") 
input_text=st.text_input("What Question you have in your mind")

#ollama model
llm=Ollama(model="gemma3:1b")
output_parser=StrOutputParser()
chain=prompt|llm|output_parser

if input_text:
    st.write(chain.invoke({"question":input_text}))

#how to run
# type in terminal   cd 2_Building_Langchain  then  streamlit run 1_InputOutput_prompt_engg_LLM.py