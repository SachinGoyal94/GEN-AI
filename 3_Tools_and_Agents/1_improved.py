
# Just a improved version of search engine but outside scope of course only class of search is outside

import streamlit as st
from langchain_groq import ChatGroq
from langchain_community.utilities import ArxivAPIWrapper,WikipediaAPIWrapper
from langchain_community.tools import ArxivQueryRun,WikipediaQueryRun,DuckDuckGoSearchRun
from langchain.agents import initialize_agent,AgentType
from langchain.callbacks import StreamlitCallbackHandler
from langchain_core.tools import BaseTool
from duckduckgo_search import DDGS
import os
from dotenv import load_dotenv
from pydantic import Field

class SafeDuckDuckGoSearch(BaseTool):
    name: str = "Search"
    description: str = "Search the web using DuckDuckGo"

    def _run(self, query: str):
        results = []
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(query):
                    results.append(r)
            return results or "No results found."
        except Exception as e:
            return f"Search failed: {str(e)}"

    async def _arun(self, query: str):
        return self._run(query)

## Arxiv and wikipedia Tools
arxiv_wrapper=ArxivAPIWrapper(top_k_results=1, doc_content_chars_max=200)
arxiv=ArxivQueryRun(api_wrapper=arxiv_wrapper)

api_wrapper=WikipediaAPIWrapper(top_k_results=1,doc_content_chars_max=200)
wiki=WikipediaQueryRun(api_wrapper=api_wrapper)

search = SafeDuckDuckGoSearch()



st.title("🔎 LangChain - Chat with search")
"""
In this example, we're using `StreamlitCallbackHandler` to display the thoughts and actions of an agent in an interactive Streamlit app.
Try more LangChain 🤝 Streamlit Agent examples at [github.com/langchain-ai/streamlit-agent](https://github.com/langchain-ai/streamlit-agent).
"""

## Sidebar for settings
st.sidebar.title("Settings")
api_key=st.sidebar.text_input("Enter your Groq API Key:",type="password")

if "messages" not in st.session_state:
    st.session_state["messages"]=[
        {"role":"assisstant","content":"Hi,I'm a chatbot who can search the web. How can I help you?"}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg['content'])

##if user query not empty then in the input box user the query and prompt gets the query
if prompt:=st.chat_input(placeholder="What is machine learning?"):   #just a suggestion to user to ask what is ml??
    st.session_state.messages.append({"role":"user","content":prompt})
    st.chat_message("user").write(prompt)

    #when streaming =True it shows how ai is responding instead of giving a response only
    llm=ChatGroq(groq_api_key=api_key,model_name="Llama3-8b-8192",streaming=True)
    tools=[search,arxiv,wiki]

    search_agent=initialize_agent(tools,llm,agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,handling_parsing_errors=True)
    # zeroshotreactdescription-->generates answer independent of chat history
    # Chatzeroshotreactdescription-->generates answer based on chat history and give error is query doesn't match with
    #                                 history
    #Handling parser explained at end of file

    with st.chat_message("assistant"):
        st_cb=StreamlitCallbackHandler(st.container(),expand_new_thoughts=False)
        response = search_agent.run(prompt, callbacks=[st_cb])

        st.session_state.messages.append({'role':'assistant',"content":response})
        st.write(response)
#expand new thought means if i want to see how ai is thingking then i click on > to see else
#just a headline #searching wikipedia


#Handling parser :
#user: what is weather in paris

# then agent sent the prompt and instructions to llm like
#     “You are an agent. You can use these tools:
#     Search: Use it to search the web.
#     follow this format
#     thought:
#     action:
#     action input :

# now when llm get this query from user it outputs like
#    Thought: The user wants the current weather in Paris. I need to search online.
#    Action: Search
#    Action Input: "weather in Paris"

# and agent parses the llm output
#    Which tool to call: Search
#    What input to send: "weather in Paris"

# agent runs the tool and  send to llm back as--> Observation: Paris is currently 23°C and sunny.

# then llm thinks
# Thought: I now know the weather.
# Final Answer: The current weather in Paris is 23°C and sunny.

# so chatbot displays
# Assistant: The current weather in Paris is 23°C and sunny.

# but what if the llm ouputs
# I think I should search: "weather in Paris"

# instead of action  action input thought

# then agent asks llm to again send the output to it in format of :: thought action action search
