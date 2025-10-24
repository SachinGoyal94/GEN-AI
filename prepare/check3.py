import requests
import os
import base64
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
apikey = os.getenv("NVIDIA_API_KEY")

if not apikey:
    raise ValueError("❌ No NVIDIA_API_KEY found in .env file")

# NVIDIA text-to-image endpoint
invoke_url = "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-dev"

headers = {
    "Authorization": f"Bearer {apikey}",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

payload = {
    "prompt": "🎯 System: GenAI Hub"
    "Main Activity Flow (User Perspective)"
    
    "Start"
    
    "User Registration/Login"
    
    "[Decision] New User? → Register"
    
    "Existing User → Login"
    
    "Access Dashboard"
    
    "Select AI Module"
    
    "Course Generator"
    
    "Blog Generator"
    
    "Code Assistant"
    
    "Math Solver"
    
    "Summarizer"
    
    "Database Chatbot"
    
    "PersonaFlow"
    
    "Provide Input (text, link, code, or query)"
    
    "Process Request"
    
    "Sent to backend (FastAPI/Flask)"
    
    "Calls respective AI model (LangChain, Gemini, OpenAI, HuggingFace)"
    
    "Generate Output"
    
    "[Decision] Is output valid?"
    
    "Yes → Proceed"
    
    "No → Retry / Modify Input"
    
    "Display Result to User"
    
    "Optional: Export / Save Output"
    
    "Save as PDF/PNG/TXT"
    
    "Logout"
    
    "End"
    
    "Admin Flow (optional parallel branch)"
    
    "Monitor system logs"
    
    "Manage users and database"

    "Update or test AI modules",
    "mode": "base",
    "cfg_scale": 3.5,
    "width": 1024,
    "height": 1024,
    "seed": 0,
    "steps": 30
}

# Send request
response = requests.post(invoke_url, headers=headers, json=payload)
response.raise_for_status()
response_body = response.json()

print("✅ Response received")

# Extract image (depends on response format)
if "artifacts" in response_body and len(response_body["artifacts"]) > 0:
    image_base64 = response_body["artifacts"][0].get("base64")
    if image_base64:
        # Decode and save
        image_bytes = base64.b64decode(image_base64)
        with open("output.png", "wb") as f:
            f.write(image_bytes)
        print("🎉 Image saved as output.png")
    else:
        print("⚠️ No base64 image found in response")
else:
    print("⚠️ Unexpected response format:", response_body)
