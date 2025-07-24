import validators,streamlit as st
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.summarize import load_summarize_chain
from langchain_community.document_loaders import UnstructuredURLLoader
from youtube_transcript_api import YouTubeTranscriptApi
from langchain.schema import Document

## streamlit APP
st.set_page_config(page_title="LangChain: Summarize Text From YT or Website", page_icon="🦜")
st.title("🦜 LangChain: Summarize Text From YT or Website")
st.subheader('Summarize URL')

import os
from dotenv import load_dotenv
load_dotenv()
gemini_api_key=os.getenv('GEMINI_KEY') or st.secrets['gemini_key']

generic_url=st.text_input("URL",label_visibility="collapsed")
llm=ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite-preview-06-17",api_key=gemini_api_key)

prompt_template="""
Provide the summary for the given content in 300 words
Content:{text}
"""
prompt=PromptTemplate(input_variables=["text"],template=prompt_template)


##youtube_link = "https://www.youtube.com/watch?v=0R1mA_MVItI"
##https://www.youtube.com/watch?v=<VIDEO_ID>   so to get video id we split

#in any yt video the transcripts of the video are stored like this
# [
#   {'text': 'hii welcome to my channel.', 'start': 0.0, 'duration': 5.0},
#   {'text': 'Today we will talk about cricket.', 'start': 5.0, 'duration': 4.0},
#   ...
# ]

selected_lang = None
# so to get the all the words i.e. captions we have to add the text part
if "youtube.com" in generic_url and validators.url(generic_url):
    try:
        video_id=generic_url.split("=")[1]


        ## getting all the transcritps in various languages
        ytt_api=YouTubeTranscriptApi()
        available_transcripts = ytt_api.list(video_id)
        lang_options=[t.language_code for t in available_transcripts]

        #let user pick the language
        selected_lang=st.selectbox("Select Language",options=lang_options)

    except Exception as e:
        raise e



if st.button("Summarize the content from Yt or website"):
    if not gemini_api_key.strip() or not generic_url.strip():
        st.error("pls provide all the informations")
    elif not validators.url(generic_url):
        st.error("pls provide a valid url")
    else:
        try:
            with st.spinner("🔍 Fetching content and generating summary..."):
                if "youtube.com" in generic_url:
                    if not selected_lang:
                        st.warning("Please select a language for the transcript first.")
                        st.stop()

                    ytt_api = YouTubeTranscriptApi()
                    transcript_data = ytt_api.fetch(video_id, languages=[selected_lang])

                    transcript_text = ""
                    for snippet in transcript_data:
                        transcript_text +=" "+ snippet.text

                    docs = [Document(page_content=transcript_text)]
                else:
                    loader=UnstructuredURLLoader(urls=[generic_url],ssl_verify=False,
                                                 headers={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"})
                    docs=loader.load()
                chain=load_summarize_chain(llm,prompt=prompt,chain_type='stuff')
                output=chain.run(docs)

                st.success(output)
        except Exception as e:
            st.error(f"Exception:{e}")
