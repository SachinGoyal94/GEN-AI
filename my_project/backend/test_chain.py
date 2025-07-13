from llm_chain import get_chain

# Test Groq
chain = get_chain("gemini-2.5-flash-lite-preview-06-17")
print(chain.invoke({"question": "Hello world"}))  # Should return a response

# Test Ollama
chain = get_chain("llama3.2:latest")
print(chain.invoke({"question": "Hello world"}))