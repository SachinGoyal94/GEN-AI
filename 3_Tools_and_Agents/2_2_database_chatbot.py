import streamlit as st
from langchain.agents import create_sql_agent
from pathlib import Path
from langchain.sql_database import SQLDatabase
from langchain.agents.agent_types import AgentType
from langchain.callbacks import StreamlitCallbackHandler
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from sqlalchemy import create_engine
import sqlite3
from langchain_groq import ChatGroq
st.set_page_config(page_title="LangChain: Chat with SQL DB",page_icon="")
st.title("🦜 LangChain: Chat with SQL DB")


#now options to select which database user want to talk with

#local database Student
LOCALDB="USE_LOCALDB"

#if user wants to provide their own database and tables
MYSQL="USE_MYSQL"

radio_opt=["Use Sqlite3 Database-students.db","Connect to your Sql Database"]
selected_opt=st.sidebar.radio(label="Choose the DB you want to use",options=radio_opt)

if radio_opt.index(selected_opt)==1:
    db_uri=MYSQL
    mysql_host=st.sidebar.text_input("Provide MySql Host")
    mysql_user=st.sidebar.text_input("Provide MySql user")
    mysql_password=st.sidebar.text_input("MySql Password",type="password")
    mysql_db=st.sidebar.text_input("Provide MySql Database")
else:
    db_uri=LOCALDB

#now user has selected which db they want to chat with

api_key=st.sidebar.text_input("Enter you Groq Key",type="password")

st.sidebar.info(
            """"💡 **Advice:** If you choose MySQL, make sure any special character in password is replaced by
            
            @	%40  
            :	%3A 
            /	%2F 
            #	%23  
            ?	%3F  
            &	%26 
        """)

if not db_uri:
    st.info("Pls enter DB info and uri")
if not api_key:
    st.info("Pls enter you Groq Key")

llm=ChatGroq(groq_api_key=api_key,model="gemma2-9b-it",streaming=True)


@st.cache_resource(ttl="2h")
def configure_db(db_uri,mysql_host=None,mysql_user=None,mysql_password=None,mysql_db=None):
    if db_uri==LOCALDB:
        dbfilepath=(Path(__file__).parent/"students.db").absolute()
        print(dbfilepath)
        creator = lambda: sqlite3.connect(f"file:{dbfilepath}?mode=ro", uri=True)
        return SQLDatabase(create_engine("sqlite:///", creator=creator))
    elif db_uri==MYSQL:
        if not (mysql_host and mysql_user and mysql_password and mysql_db):
            st.error("Please provide all MySQL connection details.")
            st.stop()
        return SQLDatabase(create_engine(f"mysql+mysqlconnector://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_db}"))

if db_uri==MYSQL:
    db=configure_db(db_uri,mysql_host,mysql_user,mysql_password,mysql_db)
else:
    db=configure_db(db_uri)

#toolkit agent
toolkit=SQLDatabaseToolkit(db=db,llm=llm)

agent=create_sql_agent(llm,toolkit,verbose=True,agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION)

if "messages" not in st.session_state or st.sidebar.button("clear message history"):
    st.session_state["messages"]=[{"role":"assistant","content":"Hii, How can i help you?"}]

user_query=st.chat_input(placeholder="Ask anything from the database")

if user_query:
    st.session_state.messages.append({"role":"assistant","content":user_query})
    st.chat_message("user").write(user_query)

    with st.chat_message("assistant"):
        streamlit_callback_handler= StreamlitCallbackHandler(st.container())
        response=agent.run(user_query,callbacks=[streamlit_callback_handler])
        st.session_state.messages.append({"role":"assistant","content":response})
        st.write(response)
