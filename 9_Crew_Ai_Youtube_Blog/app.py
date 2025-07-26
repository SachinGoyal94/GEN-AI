import gradio as gr
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import all the modules
from crewai import Agent, Crew, Process, Task, LLM
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_groq import ChatGroq
from langchain.chains.summarize import load_summarize_chain
from langchain_huggingface import HuggingFaceEmbeddings

# =======================
# TOOLS MODULE
# =======================

# Global variable to store the current character summary
_current_character_summary = ""
_current_character_name = ""


def set_character_context(character_name: str, summary: str):
    """Set the current character context for the tool to use."""
    global _current_character_summary, _current_character_name
    _current_character_summary = summary
    _current_character_name = character_name


class CharacterToolInput(BaseModel):
    """Input schema for CharacterTool."""
    query: str = Field(...,
                       description="A question or query about the character's personality, background, or behavior")


class CharacterTool(BaseTool):
    name: str = "Character Information Tool"
    description: str = (
        "Provides detailed information about the character's personality, background, and behavioral traits. "
        "Use this when you need specific details about how the character would behave, speak, or respond."
    )
    args_schema: Type[BaseModel] = CharacterToolInput

    def _run(self, query: str) -> str:
        """Execute the tool with the given query about the character."""
        if _current_character_summary and _current_character_name:
            return f"Character: {_current_character_name}\n\nCharacter Information: {_current_character_summary}\n\nFor your query '{query}': Use this character information to respond authentically as {_current_character_name}."
        else:
            return f"Character context not available. Please refer to the character's backstory in your instructions for query: {query}"


# Create the tool instance
character_tool = CharacterTool()

# =======================
# LLM MODULE
# =======================

groq_key = os.getenv("GROQ_KEY")

if not groq_key:
    raise ValueError("GROQ_KEY not found in environment variables. Please check your .env file.")

# CrewAI LLM with Groq provider
groq_llm = LLM(
    model='groq/gemma2-9b-it',
    api_key=groq_key,
    temperature=0.7
)

# =======================
# CHARACTER INFO MODULE
# =======================

# Initialize the LLM for document processing
groq_api_key = os.getenv("GROQ_KEY")

if not groq_api_key:
    raise ValueError("GROQ_KEY not found in environment variables")

# LangChain ChatGroq for document summarization
langchain_groq_llm = ChatGroq(
    model="gemma2-9b-it",
    api_key=groq_api_key,
    temperature=0.3  # Lower temperature for more focused summaries
)

# HuggingFace embeddings setup
hf_token = os.getenv('HF_TOKEN')
if hf_token:
    os.environ['HF_TOKEN'] = hf_token

try:
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
except Exception as e:
    print(f"Warning: Could not initialize HuggingFace embeddings: {e}")
    embeddings = None


def load_pdf_documents(filepath: str):
    """Load documents from PDF file."""
    try:
        loader = PyPDFLoader(filepath)
        documents = loader.load()
        return documents
    except Exception as e:
        raise Exception(f"Error loading PDF: {str(e)}")


def get_character_summary(character_name: str, pdf_path: str) -> str:
    """Generate a character summary from PDF document."""
    try:
        # Load documents
        documents = load_pdf_documents(pdf_path)

        if not documents:
            return f"No content found in the PDF for {character_name}"

        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )

        chunks = text_splitter.split_documents(documents)

        if not chunks:
            return f"No text chunks created from the PDF for {character_name}"

        # Create summarization chain
        summarize_chain = load_summarize_chain(
            llm=langchain_groq_llm,
            chain_type="map_reduce",
            verbose=True
        )

        # Generate summary
        summary = summarize_chain.run(chunks)

        # Create character-focused summary
        character_summary = f"""
        Character Profile for {character_name}:

        {summary}

        This character analysis should be used to understand {character_name}'s personality, 
        speaking style, motivations, and typical behavioral patterns for authentic roleplay.
        """

        return character_summary

    except Exception as e:
        error_msg = f"Error generating character summary for {character_name}: {str(e)}"
        print(error_msg)
        return error_msg


# =======================
# AGENTS MODULE
# =======================

def create_character_agent(character_name: str, character_summary: str, llm):
    """Create a character agent that can respond in character."""

    return Agent(
        name=f"{character_name} Character Agent",
        role=f"Character roleplay specialist for {character_name}",
        goal=f"Respond authentically as {character_name}, maintaining their personality, speech patterns, and behavioral traits",
        backstory=f"""
        You are {character_name}. Here is your character information:

        {character_summary}

        Your task is to respond to user messages exactly as {character_name} would respond.
        Stay true to the character's personality, use their typical speech patterns, 
        and maintain consistency with their established traits and background.
        """,
        tools=[character_tool],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        memory=False,
        max_iter=3
    )


# =======================
# TASKS MODULE
# =======================

def create_character_response_task(character_name: str, user_message: str, agent):
    """Create a task for the character to respond to the user's message."""

    return Task(
        description=f"""
        You are {character_name}. The user has sent you this message: "{user_message}"

        Your task is to respond exactly as {character_name} would respond to this message.

        Guidelines:
        1. Stay completely in character as {character_name}
        2. Use their typical speech patterns and vocabulary
        3. Respond based on their personality traits and background
        4. Be authentic to how {character_name} would actually react
        5. If you need more information about the character, use the Character Information Tool

        Respond naturally and conversationally as {character_name}.
        """,
        expected_output=f"""
        A natural, authentic response from {character_name} to the user's message.
        The response should:
        - Sound like {character_name} is actually speaking
        - Reflect their personality and character traits
        - Be appropriate to their background and context
        - Feel like a genuine conversation
        """,
        tools=[character_tool],
        agent=agent
    )


# =======================
# CREW MODULE
# =======================

def build_character_crew(character_name: str, character_summary: str, user_message: str, llm):
    """Build a crew for character interaction."""

    # Set the character context for the tool
    set_character_context(character_name, character_summary)

    # Create the character agent
    agent = create_character_agent(character_name, character_summary, llm)

    # Create the response task
    task = create_character_response_task(character_name, user_message, agent)

    # Create and return the crew
    return Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
        memory=False
    )


# =======================
# GRADIO APPLICATION
# =======================

# Global state variables
character_summary = ""
character_name = ""
pdf_processed = False
chat_history = []


def process_character(character_name_input, uploaded_file):
    """Process the uploaded PDF and character name"""
    global character_summary, character_name, pdf_processed, chat_history

    if not uploaded_file or not character_name_input:
        return (
            "❌ Please provide both a character name and upload a PDF file.",
            "",
            gr.update(visible=False),
            gr.update(visible=False),
            []
        )

    try:
        # Create directory for character documents
        os.makedirs("character_docs", exist_ok=True)

        # Save uploaded file
        file_path = f"character_docs/{character_name_input}_document.pdf"
        with open(file_path, "wb") as f:
            f.write(uploaded_file)

        summary = get_character_summary(character_name_input, file_path)

        character_summary = summary
        character_name = character_name_input
        pdf_processed = True
        chat_history = []  # Clear previous chat history

        return (
            f"✅ {character_name} is ready to chat!",
            summary,
            gr.update(visible=True),
            gr.update(visible=True),
            []
        )

    except Exception as e:
        return (
            f"❌ Error processing character: {str(e)}",
            "",
            gr.update(visible=False),
            gr.update(visible=False),
            []
        )


def clear_character():
    """Clear all character data"""
    global character_summary, character_name, pdf_processed, chat_history

    character_summary = ""
    character_name = ""
    pdf_processed = False
    chat_history = []

    return (
        "",  # character name
        None,  # uploaded file
        "Character cleared. Please set up a new character.",  # status
        "",  # character summary
        gr.update(visible=False),  # chat interface
        gr.update(visible=False),  # summary display
        []  # chat history
    )


def send_message(user_input):
    """Send message to character and get response"""
    global chat_history, character_name, character_summary

    if not pdf_processed or not user_input.strip():
        return chat_history, ""

    try:
        crew = build_character_crew(
            character_name,
            character_summary,
            user_input,
            groq_llm
        )

        result = crew.kickoff()

        if hasattr(result, 'raw'):
            character_response = result.raw
        else:
            character_response = str(result)

        # Add to chat history
        chat_history.append([user_input, character_response])

        return chat_history, ""

    except Exception as e:
        error_msg = f"❌ Error getting response: {str(e)}. Please check your API key and try again."
        chat_history.append([user_input, error_msg])
        return chat_history, ""


def clear_chat():
    """Clear chat history"""
    global chat_history
    chat_history = []
    return []


# Create Gradio interface
with gr.Blocks(theme=gr.themes.Soft(primary_hue="violet").set(
        body_background_fill="*neutral_950",
        body_background_fill_dark="*neutral_950",
        background_fill_primary="*neutral_900",
        background_fill_primary_dark="*neutral_900",
        background_fill_secondary="*neutral_800",
        background_fill_secondary_dark="*neutral_800",
        border_color_primary="*neutral_700",
        border_color_primary_dark="*neutral_700",
        button_primary_background_fill="*violet_600",
        button_primary_background_fill_dark="*violet_600",
        button_primary_text_color="white",
        button_primary_text_color_dark="white"
), title="🧙‍♂️ Character Chat") as app:
    gr.Markdown("""
    # 🧙‍♂️ Character Chat from Any Book or Movie
    Upload a PDF of a book or script and chat with any character from it!

    **Required Environment Variables:**
    - `GROQ_KEY`: Your Groq API key
    - `HF_TOKEN`: Your HuggingFace token (optional)
    """)

    with gr.Row():
        # Left column for character setup
        with gr.Column(scale=1):
            gr.Markdown("## 📚 Character Setup")

            character_name_input = gr.Textbox(
                label="Character Name",
                placeholder="Enter the name of the character you want to chat with"
            )

            uploaded_file = gr.File(
                label="Upload Character Document (PDF)",
                file_types=[".pdf"]
            )

            gr.Markdown("💡 Upload a PDF containing information about the character")

            with gr.Row():
                process_btn = gr.Button("🔄 Process Character", variant="primary")
                clear_btn = gr.Button("🗑️ Clear Character", variant="secondary")

            status_msg = gr.Textbox(
                label="Status",
                interactive=False,
                value="Please upload a PDF and enter a character name to get started."
            )

            character_summary_display = gr.Textbox(
                label="📄 Character Summary",
                lines=8,
                interactive=False,
                visible=False
            )

        # Right column for chat interface
        with gr.Column(scale=2):
            gr.Markdown("## 💬 Chat Interface")

            chatbot = gr.Chatbot(
                label="Chat History",
                height=400,
                visible=False,
                avatar_images=("👤", "🧙‍♂️")
            )

            with gr.Row(visible=False) as chat_interface:
                with gr.Column(scale=4):
                    msg_input = gr.Textbox(
                        label="Your Message",
                        placeholder="Type your message here...",
                        lines=2
                    )
                with gr.Column(scale=1):
                    send_btn = gr.Button("Send 📤", variant="primary")
                    clear_chat_btn = gr.Button("Clear Chat 🗑️", variant="secondary")

    gr.Markdown("""
    ---
    Built with ❤️ using CrewAI, LangChain, and Gradio

    **Setup Instructions:**
    1. Create a `.env` file with your API keys:
       ```
       GROQ_KEY=your_groq_api_key_here
       HF_TOKEN=your_huggingface_token_here
       ```
    2. Install required packages:
       ```bash
       pip install gradio crewai langchain langchain-community langchain-groq langchain-huggingface pypdf python-dotenv
       ```
    """)

    # Event handlers
    process_btn.click(
        fn=process_character,
        inputs=[character_name_input, uploaded_file],
        outputs=[status_msg, character_summary_display, chat_interface, chatbot, chatbot]
    )

    clear_btn.click(
        fn=clear_character,
        outputs=[character_name_input, uploaded_file, status_msg, character_summary_display, chat_interface, chatbot,
                 chatbot]
    )

    send_btn.click(
        fn=send_message,
        inputs=[msg_input],
        outputs=[chatbot, msg_input]
    )

    msg_input.submit(
        fn=send_message,
        inputs=[msg_input],
        outputs=[chatbot, msg_input]
    )

    clear_chat_btn.click(
        fn=clear_chat,
        outputs=[chatbot]
    )

if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        debug=True
    )