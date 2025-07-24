import validators
import streamlit as st
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.summarize import load_summarize_chain
from langchain_community.document_loaders import UnstructuredURLLoader
from youtube_transcript_api import YouTubeTranscriptApi
from langchain.schema import Document
import time

# Custom CSS for animations and styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

    .main {
        font-family: 'Poppins', sans-serif;
    }

    /* Animated gradient background - darker and more readable */
    .stApp {
        background: linear-gradient(-45deg, #1a1a2e, #16213e, #0f3460, #533483);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
    }

    @keyframes gradientBG {
        0% {
            background-position: 0% 50%;
        }
        50% {
            background-position: 100% 50%;
        }
        100% {
            background-position: 0% 50%;
        }
    }

    /* Glass morphism container - enhanced readability */
    .main-container {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(15px);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }

    /* Animated title - better contrast */
    .animated-title {
        background: linear-gradient(45deg, #64b5f6, #81c784, #ffb74d, #f06292);
        background-size: 400% 400%;
        animation: gradientText 3s ease infinite;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 1rem;
    }

    @keyframes gradientText {
        0%, 100% {
            background-position: 0% 50%;
        }
        50% {
            background-position: 100% 50%;
        }
    }

    /* Floating animation */
    .floating {
        animation: floating 3s ease-in-out infinite;
    }

    @keyframes floating {
        0%, 100% {
            transform: translateY(0px);
        }
        50% {
            transform: translateY(-10px);
        }
    }

    /* Pulse animation for buttons */
    .stButton > button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 50px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px 0 rgba(102, 126, 234, 0.75);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 7px 25px 0 rgba(102, 126, 234, 0.9);
        animation: pulse 1s infinite;
    }

    @keyframes pulse {
        0% {
            box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.7);
        }
        70% {
            box-shadow: 0 0 0 10px rgba(102, 126, 234, 0);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(102, 126, 234, 0);
        }
    }

    /* Custom input styling - better readability */
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.08);
        border: 2px solid rgba(255, 255, 255, 0.15);
        border-radius: 15px;
        color: white !important;
        backdrop-filter: blur(15px);
        transition: all 0.3s ease;
        padding: 0.75rem 1rem;
    }

    .stTextInput > div > div > input:focus {
        border-color: #64b5f6;
        box-shadow: 0 0 20px rgba(100, 181, 246, 0.3);
        transform: scale(1.02);
        background: rgba(255, 255, 255, 0.12);
    }

    .stTextInput > div > div > input::placeholder {
        color: rgba(255, 255, 255, 0.6) !important;
    }

    /* Custom selectbox styling - better visibility */
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 15px;
        backdrop-filter: blur(15px);
        border: 2px solid rgba(255, 255, 255, 0.15);
    }

    .stSelectbox > div > div > div {
        color: white !important;
    }

    /* Success/Error message animations */
    .stSuccess {
        animation: slideInFromRight 0.5s ease-out;
        background: rgba(76, 175, 80, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        border-left: 5px solid #4caf50;
    }

    .stError {
        animation: shake 0.5s ease-out;
        background: rgba(244, 67, 54, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        border-left: 5px solid #f44336;
    }

    @keyframes slideInFromRight {
        0% {
            transform: translateX(100%);
            opacity: 0;
        }
        100% {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes shake {
        0%, 100% {
            transform: translateX(0);
        }
        10%, 30%, 50%, 70%, 90% {
            transform: translateX(-5px);
        }
        20%, 40%, 60%, 80% {
            transform: translateX(5px);
        }
    }

    /* Spinner customization */
    .stSpinner {
        text-align: center;
    }

    /* Feature cards - better visibility */
    .feature-card {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(15px);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }

    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        background: rgba(255, 255, 255, 0.12);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
    }

    ::-webkit-scrollbar-thumb {
        background: rgba(102, 126, 234, 0.8);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: rgba(102, 126, 234, 1);
    }
</style>
""", unsafe_allow_html=True)

st.set_page_config(
    page_title="AI Content Summarizer",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def create_txt_download(summary_text, url):
    """Create a TXT download for the summary"""
    content = f"""AI Content Summary
==================

Source URL: {url}

Generated Summary:
{summary_text}

---
Generated by AI Content Summarizer
"""
    return content


# Main container with glass morphism effect
st.markdown('<div class="main-container">', unsafe_allow_html=True)

st.markdown('<h1 class="animated-title floating">🚀 AI Content Summarizer</h1>', unsafe_allow_html=True)

# Subtitle with emoji
st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <h3 style="color: white; font-weight: 300;">
        ✨ Powered by Google Gemini & LangChain ✨
    </h3>
    <p style="color: rgba(255, 255, 255, 0.8); font-size: 1.1rem;">
        Transform YouTube videos and web articles into concise summaries
    </p>
</div>
""", unsafe_allow_html=True)

# Feature cards
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <h4 style="color: #64b5f6; text-align: center;">📺 YouTube Videos</h4>
        <p style="color: rgba(255, 255, 255, 0.9); text-align: center;">
            Extract and summarize video transcripts in multiple languages
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <h4 style="color: #64b5f6; text-align: center;">🌐 Web Articles</h4>
        <p style="color: rgba(255, 255, 255, 0.9); text-align: center;">
            Summarize content from any website or blog post
        </p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <h4 style="color: #64b5f6; text-align: center;">🤖 AI Powered</h4>
        <p style="color: rgba(255, 255, 255, 0.9); text-align: center;">
            Advanced AI creates intelligent, concise summaries
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

import os
from dotenv import load_dotenv

load_dotenv()
gemini_api_key = os.getenv('GEMINI_KEY') or st.secrets.get('gemini_key', '')

st.markdown("### 🔗 Enter URL to Summarize")
generic_url = st.text_input(
    "Paste your YouTube video or website URL here...",
    placeholder="https://www.youtube.com/watch?v=... or https://example.com/article",
    help="Supports YouTube videos and web articles"
)

# Important tip for YouTube videos
st.markdown("""
<div style="
    background: rgba(255, 193, 7, 0.1);
    padding: 1rem;
    border-radius: 10px;
    border-left: 4px solid #ffc107;
    margin: 1rem 0;
">
    <strong style="color: #ffc107;">💡 YouTube Video Tip:</strong>
    <span style="color: rgba(255, 255, 255, 0.9);">
        Only videos with available transcriptions/captions can be summarized. 
        Make sure the video has auto-generated or manual captions enabled.
    </span>
</div>
""", unsafe_allow_html=True)

if gemini_api_key:
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite-preview-06-17",
        api_key=gemini_api_key
    )

prompt_template = """
Provide a comprehensive and well-structured summary for the given content in approximately 300 words.
Include key points, main arguments, and important insights.

Content: {text}

Summary:
"""
prompt = PromptTemplate(input_variables=["text"], template=prompt_template)

selected_lang = None

if generic_url and "youtube.com" in generic_url and validators.url(generic_url):
    try:
        with st.spinner("🔍 Analyzing YouTube video..."):
            video_id = generic_url.split("=")[1]
            ytt_api = YouTubeTranscriptApi()
            available_transcripts = ytt_api.list(video_id)
            lang_options = [t.language_code for t in available_transcripts]

        st.markdown("### 🌍 Select Transcript Language")
        selected_lang = st.selectbox(
            "Choose the language for video transcript:",
            options=lang_options,
            help="Select the language of the video transcript you want to summarize"
        )

        st.info(f"📹 Video detected! Available in {len(lang_options)} languages.")

    except Exception as e:
        st.error(f"❌ Error accessing YouTube video: {str(e)}")

st.markdown("<br>", unsafe_allow_html=True)

if st.button("✨ Generate Summary", type="primary"):
    if not gemini_api_key.strip():
        st.error("🔑 Please provide your Gemini API key in environment variables or Streamlit secrets")
    elif not generic_url.strip():
        st.error("📝 Please enter a valid URL to summarize")
    elif not validators.url(generic_url):
        st.error("🚫 Please provide a valid URL format (must include https://)")
    else:
        try:
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()

            with st.spinner("🚀 Processing your content..."):
                progress_bar.progress(20)
                status_text.text("📥 Fetching content...")

                if "youtube.com" in generic_url:
                    if not selected_lang:
                        st.warning("⚠️ Please select a language for the transcript first.")
                        st.stop()

                    progress_bar.progress(40)
                    status_text.text("📺 Extracting YouTube transcript...")

                    ytt_api = YouTubeTranscriptApi()
                    transcript_data = ytt_api.fetch(video_id, languages=[selected_lang])

                    transcript_text = ""
                    for snippet in transcript_data:
                        transcript_text += " " + snippet.text

                    docs = [Document(page_content=transcript_text)]

                else:
                    progress_bar.progress(40)
                    status_text.text("🌐 Loading website content...")

                    loader = UnstructuredURLLoader(
                        urls=[generic_url],
                        ssl_verify=False,
                        headers={
                            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
                        }
                    )
                    docs = loader.load()

                progress_bar.progress(70)
                status_text.text("🤖 Generating AI summary...")

                chain = load_summarize_chain(llm, prompt=prompt, chain_type='stuff')
                output = chain.run(docs)

                progress_bar.progress(100)
                status_text.text("✅ Summary complete!")

                time.sleep(0.5)  # Brief pause for effect
                progress_bar.empty()
                status_text.empty()

                # Display results with animation
                st.markdown("### 📋 Summary Results")

                # Summary container with styling
                st.markdown("""
                <div style="
                    background: rgba(255, 255, 255, 0.08);
                    backdrop-filter: blur(15px);
                    border-radius: 15px;
                    padding: 2rem;
                    margin: 1rem 0;
                    border-left: 5px solid #4caf50;
                    animation: slideInFromRight 0.5s ease-out;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
                ">
                """, unsafe_allow_html=True)

                st.success("🎉 Summary generated successfully!")
                st.markdown(f"""
                <div style="
                    color: rgba(255, 255, 255, 0.95);
                    font-size: 1.1rem;
                    line-height: 1.6;
                    text-align: justify;
                    padding: 1rem 0;
                ">
                {output}
                </div>
                """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

                # Download Section
                st.markdown("### 📥 Download Summary")

                col1, col2 = st.columns([1, 2])

                with col1:
                    # TXT Download only
                    txt_content = create_txt_download(output, generic_url)
                    st.download_button(
                        label="📝 Download as TXT",
                        data=txt_content,
                        file_name=f"summary_{int(time.time())}.txt",
                        mime="text/plain",
                        help="Download summary as text file"
                    )

                with col2:
                    st.markdown("""
                    <div style="
                        background: rgba(100, 181, 246, 0.1);
                        padding: 1rem;
                        border-radius: 10px;
                        border-left: 4px solid #64b5f6;
                        margin-top: 0.5rem;
                    ">
                        <small style="color: rgba(255, 255, 255, 0.8);">
                            💡 <strong>Tip:</strong> Download your summary as a text file to keep a permanent copy 
                            for future reference, sharing, or further editing!
                        </small>
                    </div>
                    """, unsafe_allow_html=True)

                # Additional info with better styling
                st.markdown("<br>", unsafe_allow_html=True)
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"""
                    <div style="
                        background: rgba(76, 175, 80, 0.1);
                        padding: 1rem;
                        border-radius: 10px;
                        text-align: center;
                        border: 1px solid rgba(76, 175, 80, 0.3);
                    ">
                        <h4 style="color: #4caf50; margin: 0;">📊 Word Count</h4>
                        <p style="color: white; margin: 0; font-size: 1.2rem;">{len(output.split())} words</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    content_type = "YouTube Video" if "youtube.com" in generic_url else "Website"
                    st.markdown(f"""
                    <div style="
                        background: rgba(33, 150, 243, 0.1);
                        padding: 1rem;
                        border-radius: 10px;
                        text-align: center;
                        border: 1px solid rgba(33, 150, 243, 0.3);
                    ">
                        <h4 style="color: #2196f3; margin: 0;">📄 Source Type</h4>
                        <p style="color: white; margin: 0; font-size: 1.2rem;">{content_type}</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col3:
                    st.markdown(f"""
                    <div style="
                        background: rgba(255, 152, 0, 0.1);
                        padding: 1rem;
                        border-radius: 10px;
                        text-align: center;
                        border: 1px solid rgba(255, 152, 0, 0.3);
                    ">
                        <h4 style="color: #ff9800; margin: 0;">⏱️ Processing</h4>
                        <p style="color: white; margin: 0; font-size: 1.2rem;">Complete</p>
                    </div>
                    """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
            st.markdown("""
            <div style="margin-top: 1rem;">
                <details>
                    <summary style="color: #ff6b6b;">🔧 Troubleshooting Tips</summary>
                    <ul style="color: rgba(255, 255, 255, 0.8); margin-top: 0.5rem;">
                        <li>Ensure your URL is valid and accessible</li>
                        <li>Check if the YouTube video has available transcripts</li>
                        <li>Verify your Gemini API key is correctly configured</li>
                        <li>Try with a different URL if the issue persists</li>
                    </ul>
                </details>
            </div>
            """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; color: rgba(255, 255, 255, 0.8); margin-top: 3rem;">
    <p>Made with ❤️ using Streamlit, LangChain & Google Gemini</p>
    <p style="font-size: 0.8rem;">🚀 Enhancing productivity through AI-powered summarization</p>
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)