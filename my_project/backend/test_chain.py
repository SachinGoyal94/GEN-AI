from llm_chain import get_chain

# Test Groq
chain = get_chain("llama3-8b-8192")
print(chain.invoke({"question": "Hello world"}))  # Should return a response

# Test Ollama
chain = get_chain("llama3.2")
print(chain.invoke({"question": "Hello world"}))