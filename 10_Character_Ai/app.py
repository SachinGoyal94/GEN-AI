import gradio as gr
import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_groq import ChatGroq
from langchain.chains.summarize import load_summarize_chain
from langchain_huggingface import HuggingFaceEmbeddings

# Load environment variables
load_dotenv()

# Initialize API keys
groq_api_key = os.getenv("GROQ_KEY")
hf_token = os.getenv('HF_TOKEN')

if not groq_api_key:
    raise ValueError("GROQ_KEY not found in environment variables")

if hf_token:
    os.environ['HF_TOKEN'] = hf_token

# Initialize LLMs and embeddings
langchain_groq_llm = ChatGroq(
    model="gemma2-9b-it",
    api_key=groq_api_key,
    temperature=0.3
)

groq_llm = LLM(
    model='groq/gemma2-9b-it',
    api_key=groq_api_key,
    temperature=0.7
)

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Global variables for character context
_current_character_summary = ""
_current_character_name = ""


def set_character_context(character_name: str, summary: str):
    """Set the current character context for the tool to use."""
    global _current_character_summary, _current_character_name
    _current_character_summary = summary
    _current_character_name = character_name


# Character Tool Implementation
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
        print(f"🔄 Loading PDF documents for {character_name}...")
        # Load documents
        documents = load_pdf_documents(pdf_path)

        if not documents:
            return f"No content found in the PDF for {character_name}"

        print(f"📄 Loaded {len(documents)} pages. Splitting into chunks...")
        # Split documents into chunks (optimized for faster processing)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,  # Increased chunk size for fewer chunks
            chunk_overlap=100,  # Reduced overlap for faster processing
            length_function=len
        )

        chunks = text_splitter.split_documents(documents)

        if not chunks:
            return f"No text chunks created from the PDF for {character_name}"

        print(f"🔍 Created {len(chunks)} chunks. Generating character summary...")

        # Limit chunks for faster processing (take first 10 chunks if more than 10)
        if len(chunks) > 10:
            chunks = chunks[:10]
            print(f"⚡ Optimized: Using first 10 chunks for faster processing")

        # Create summarization chain with faster settings
        summarize_chain = load_summarize_chain(
            llm=langchain_groq_llm,
            chain_type="stuff",  # Changed to "stuff" for faster processing with fewer chunks
            verbose=False  # Reduced verbosity for cleaner output
        )

        print("🤖 Generating AI summary...")
        # Generate summary
        summary = summarize_chain.run(chunks)

        # Create character-focused summary
        character_summary = f"""
        Character Profile for {character_name}:

        {summary}

        This character analysis should be used to understand {character_name}'s personality, 
        speaking style, motivations, and typical behavioral patterns for authentic roleplay.
        """

        print(f"✅ Character summary generated successfully for {character_name}")
        return character_summary

    except Exception as e:
        error_msg = f"Error generating character summary for {character_name}: {str(e)}"
        print(error_msg)
        return error_msg


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


# Global state variables
character_summary = ""
character_name = ""
pdf_processed = False
chat_history = []

# Custom CSS for black and red theme
custom_css = """
/* Main background */
.gradio-container {
    background: linear-gradient(135deg, #0d0d0d 0%, #1a0a0a 100%) !important;
    color: #ffffff !important;
}

/* Header styling */
.gr-markdown h1 {
    color: #ff3333 !important;
    text-align: center !important;
    font-weight: bold !important;
    text-shadow: 0 0 10px rgba(255, 51, 51, 0.5) !important;
    margin-bottom: 20px !important;
}

.gr-markdown h2 {
    color: #ff6666 !important;
    border-bottom: 2px solid #ff3333 !important;
    padding-bottom: 10px !important;
}

.gr-markdown h3 {
    color: #ff9999 !important;
    text-align: center !important;
}

/* Input components */
.gr-textbox, .gr-textarea {
    background: rgba(20, 20, 20, 0.8) !important;
    border: 2px solid #333333 !important;
    color: #ffffff !important;
    border-radius: 10px !important;
}

.gr-textbox:focus, .gr-textarea:focus {
    border-color: #ff3333 !important;
    box-shadow: 0 0 10px rgba(255, 51, 51, 0.3) !important;
}

/* Buttons */
.gr-button {
    background: linear-gradient(135deg, #ff3333 0%, #cc0000 100%) !important;
    border: none !important;
    color: white !important;
    font-weight: bold !important;
    border-radius: 10px !important;
    transition: all 0.3s ease !important;
}

.gr-button:hover {
    background: linear-gradient(135deg, #ff5555 0%, #ee0000 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 5px 15px rgba(255, 51, 51, 0.4) !important;
}

.gr-button.secondary {
    background: linear-gradient(135deg, #333333 0%, #1a1a1a 100%) !important;
    border: 2px solid #ff3333 !important;
}

/* File upload */
.gr-file-upload {
    background: rgba(20, 20, 20, 0.8) !important;
    border: 2px dashed #ff3333 !important;
    border-radius: 10px !important;
    color: #ffffff !important;
}

/* Chat history */
.gr-chatbot {
    background: rgba(10, 10, 10, 0.9) !important;
    border: 2px solid #333333 !important;
    border-radius: 15px !important;
}

.gr-chatbot .message {
    background: rgba(255, 51, 51, 0.1) !important;
    border-left: 4px solid #ff3333 !important;
    margin: 10px 0 !important;
    padding: 15px !important;
    border-radius: 10px !important;
}

/* Accordion/Expandable sections */
.gr-accordion {
    background: rgba(20, 20, 20, 0.8) !important;
    border: 1px solid #333333 !important;
    border-radius: 10px !important;
}

/* Status messages */
.gr-info {
    background: rgba(255, 51, 51, 0.2) !important;
    border: 1px solid #ff3333 !important;
    color: #ffffff !important;
    border-radius: 10px !important;
}

/* Tabs */
.gr-tab-nav {
    background: rgba(20, 20, 20, 0.8) !important;
    border-bottom: 2px solid #ff3333 !important;
}

.gr-tab-nav button {
    background: transparent !important;
    color: #ffffff !important;
    border: none !important;
}

.gr-tab-nav button.selected {
    background: linear-gradient(135deg, #ff3333 0%, #cc0000 100%) !important;
    color: white !important;
}

/* Loading spinner */
.gr-loading {
    color: #ff3333 !important;
}

/* Scrollbar styling */
::-webkit-scrollbar {
    width: 12px;
}

::-webkit-scrollbar-track {
    background: #1a1a1a;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #ff3333 0%, #cc0000 100%);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #ff5555 0%, #ee0000 100%);
}

/* Footer styling */
.footer {
    background: rgba(20, 20, 20, 0.8) !important;
    border-top: 2px solid #ff3333 !important;
    padding: 20px !important;
    text-align: center !important;
    color: #ff6666 !important;
}
"""


def process_character(character_name_input, uploaded_file):
    """Process the uploaded character document"""
    global character_summary, character_name, pdf_processed, chat_history

    if not uploaded_file or not character_name_input:
        return (
            "❌ Please provide both a character name and upload a PDF file.",
            "",
            gr.update(visible=False),  # Hide character info
            gr.update(visible=False),  # Hide chat interface
            [],  # Clear chat
            "📋 Please upload a character document to get started."  # Processing status
        )

    try:
        # Create directory for character documents
        os.makedirs("character_docs", exist_ok=True)

        # Save uploaded file
        file_path = f"character_docs/{character_name_input}_document.pdf"
        with open(file_path, "wb") as f:
            f.write(uploaded_file)

        summary = get_character_summary(character_name_input, file_path)

        # Update global state
        character_summary = summary
        character_name = character_name_input
        pdf_processed = True
        chat_history = []

        return (
            f"✅ {character_name_input} is ready to chat!",
            summary,
            gr.update(visible=True),  # Show character info
            gr.update(visible=True),  # Show chat interface
            [],  # Clear chat history
            f"✅ Processing complete! {character_name_input} is ready."  # Processing status
        )

    except Exception as e:
        return (
            f"❌ Error processing character: {str(e)}",
            "",
            gr.update(visible=False),
            gr.update(visible=False),
            [],
            f"❌ Processing failed: {str(e)}"  # Processing status
        )


def clear_character():
    """Clear all character data"""
    global character_summary, character_name, pdf_processed, chat_history

    character_summary = ""
    character_name = ""
    pdf_processed = False
    chat_history = []

    return (
        "🗑️ Character cleared. Please upload a new character to start chatting.",
        "",
        "",
        gr.update(visible=False),  # Hide character info
        gr.update(visible=False),  # Hide chat interface
        []  # Clear chat
    )


def chat_with_character(message, history):
    """Handle chat with the character"""
    global character_summary, character_name

    if not pdf_processed or not message.strip():
        return history, ""

    try:
        crew = build_character_crew(
            character_name,
            character_summary,
            message,
            groq_llm
        )

        result = crew.kickoff()

        if hasattr(result, 'raw'):
            character_response = result.raw
        else:
            character_response = str(result)

        # Add to history
        history.append([message, character_response])

        return history, ""

    except Exception as e:
        error_message = f"❌ Error getting response: {str(e)}\nPlease check your API key and try again."
        history.append([message, error_message])
        return history, ""


def clear_chat():
    """Clear chat history"""
    return []


# Create the Gradio interface
with gr.Blocks(css=custom_css, theme=gr.themes.Base(), title="Character Chat 💬") as app:
    gr.Markdown("""
    # 🧙‍♂️ Character Chat from Any Book or Movie
    ### Upload a PDF of a book or script and chat with any character from it!
    """)

    with gr.Row():
        # Left column - Character Setup
        with gr.Column(scale=1):
            gr.Markdown("## 📚 Character Setup")

            character_name_input = gr.Textbox(
                label="🎭 Character Name",
                placeholder="Enter the name of the character you want to chat with",
                interactive=True
            )

            uploaded_file = gr.File(
                label="📖 Upload Character Document (PDF)",
                file_types=[".pdf"],
                type="binary"
            )

            with gr.Row():
                process_btn = gr.Button("🔄 Process Character", variant="primary")
                clear_btn = gr.Button("🗑️ Clear Character", variant="secondary")

            status_message = gr.Markdown("📋 Please upload a character document to get started.")

            # Character information (initially hidden)
            character_info = gr.Accordion("📄 Character Summary", visible=False)
            with character_info:
                character_summary_display = gr.Textbox(
                    label="Character Information",
                    lines=8,
                    interactive=False
                )

        # Right column - Chat Interface
        with gr.Column(scale=2):
            chat_interface = gr.Group(visible=False)
            with chat_interface:
                gr.Markdown("## 💬 Chat Interface")

                chatbot = gr.Chatbot(
                    label="Chat History",
                    height=400,
                    bubble_full_width=False,
                    show_label=True
                )

                with gr.Row():
                    msg_input = gr.Textbox(
                        label="Your Message",
                        placeholder="Type your message here...",
                        lines=2,
                        scale=4
                    )
                    with gr.Column(scale=1):
                        send_btn = gr.Button("📤 Send", variant="primary")
                        clear_chat_btn = gr.Button("🗑️ Clear Chat", variant="secondary")

    # Footer
    gr.Markdown("""
    ---
    <div class="footer">
        Built with ❤️ using CrewAI, LangChain, and Gradio
    </div>
    """)

    # Event handlers
    process_btn.click(
        fn=process_character,
        inputs=[character_name_input, uploaded_file],
        outputs=[status_message, character_summary_display, character_info, chat_interface, chatbot]
    )

    clear_btn.click(
        fn=clear_character,
        inputs=[],
        outputs=[status_message, character_name_input, character_summary_display, character_info, chat_interface,
                 chatbot]
    )

    send_btn.click(
        fn=chat_with_character,
        inputs=[msg_input, chatbot],
        outputs=[chatbot, msg_input]
    )

    msg_input.submit(
        fn=chat_with_character,
        inputs=[msg_input, chatbot],
        outputs=[chatbot, msg_input]
    )

    clear_chat_btn.click(
        fn=clear_chat,
        inputs=[],
        outputs=[chatbot]
    )

# Launch the app
if __name__ == "__main__":
    app.launch(
        server_name="localhost",
#        server_port=7860,
        share=False,
        debug=True
    )