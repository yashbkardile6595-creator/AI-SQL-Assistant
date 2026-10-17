
from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="llama3:8b",
    temperature=0
)

question = "Write a SQL query to show all employees earning more than 50000."

response = llm.invoke(question)

print("\nAI RESPONSE:")
print(response.content)
