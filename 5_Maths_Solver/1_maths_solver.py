import streamlit as st
from langchain_groq import ChatGroq
from langchain.chains import LLMMathChain,LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.agents.agent_types import AgentType
from langchain.agents import Tool,initialize_agent
from langchain.callbacks import StreamlitCallbackHandler

st.set_page_config(page_title="Text to Maths Solver",page_icon="🧮")
st.title("Text to Maths Problem Solver Using Google Gemma 2")
groq_api_key=st.sidebar.text_input(label="Enter Groq API Key",type="password")

if not groq_api_key:
    st.info("Please enter Groq API Key")
    st.stop()

llm=ChatGroq(model="Gemma2-9b-It",api_key=groq_api_key)

# Option 1: Specialized tools done in 3_tools_agents
# * wiki_tool = WikipediaQueryRun(...) → pulls factual info
# * solver_tool = ThirdPartyProblemSolverRun(...) → computes numerical answers
# option 2 used here
# wiki_tool = Tool(
#    name="Wikipedia",
#    func=wikipedia_wrapper.run,
#    description="Use this to get factual information, formulas, and theory needed for explanations."
# )
# solver_tool = Tool(
#    name="TriangleSolver",
#    func=third_party_solver.run,
#    description="Use this to perform numerical calculations when the problem requires a final answer."
# )
# let me give you a  example suppose
# first condition i provide wikiqueryrun and thirdpartyproblemsolverrun right
# and i gave prompt in prompt template to ai that i need answer as well as exaplanation to the solution provided
# here as obv wikipedia can provide area of triangle
# but agent need to use thirdpartyprobmelm solver run to get the numerical output
# here there is a chance of deadlock as info comes from wiki solution from third party
#
# but
# if generalise them with the description then agent gets formula of triangle from wiki to provide explanation and asnwer from third party tool distributing the workigs


wikipedia_wrap=WikipediaAPIWrapper()
wiki_tool=Tool(name="Wikipedia",func=wikipedia_wrap.run,description="Wikipedia Tool to find info related to the problem topics")

#initializing maths tool
math_chain=LLMMathChain.from_llm(llm)
calculator=Tool(name="Calculator",
                func=math_chain.run,
                description="A tools for answering math related questions. Only input mathematical expression need to bed provided")

prompt="""
Your a agent tasked for solving users mathemtical question. Logically arrive at the solution and provide a detailed explanation
and display it point wise for the question below
Question:{question}
Answer:
"""
prompt_template=PromptTemplate(input_variables=['question'],template=prompt)

chain=LLMChain(llm=llm,prompt=prompt_template)

reasoning_tool=Tool(name="Reasoning tool",
                    func=chain.run,
                    description="a tool which can solve and provide answer to the user question")

# initialising agents

assistant_agent=initialize_agent(
    tools=[wiki_tool,calculator,reasoning_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=False,
    handle_parsing_errors=True
)

if "messages" not in st.session_state:
    st.session_state["messages"]=[
        {"role":"assistant","content":"Hii ,i'm a Math Chatbot who can help you with all your maths problems"}
    ]

#to show the chat continuosly not only latest query and response
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

question=st.text_area("Enter your Question : ","I have 5 bananas and 7 grapes. I eat 2 bananas and give away 3 grapes. Then I buy a dozen apples and 2 packs of blueberries. Each pack of blueberries contains 25 berries. How many total pieces of fruit do I have at the end?")

if st.button("find my answer"):
    if question:
        with st.spinner("Finding..."):
            st.session_state.messages.append({"role":"user","content":question})
            st.chat_message("user").write(question)

            st_cb=StreamlitCallbackHandler(st.container(),expand_new_thoughts=False) #displaying agent's thought
            result=assistant_agent.run(st.session_state.messages,callbacks=[st_cb])

            if isinstance(result, dict) and "output" in result:
                response = result["output"]
            else:
                response = result
                
            st.session_state.messages.append({"role":"assistant","content":response})
            st.write("Response:")
            st.success(response)
    else:
        st.warning("Please enter a question")
