import os
from dotenv import load_dotenv
from openai import OpenAI
import ollama

# Define default headers for HTTP requests
load_dotenv(override=True)
api_key = os.getenv("OPENAI_API_KEY")

if api_key and api_key.startswith("sk-proj-") and len(api_key) > 10:
    print("API key looks good so far")
else:
    print(
        "There might be a problem with your API key? Please visit the troubleshooting notebook!"
    )

MODEL = "gpt-4o-mini"
openai = OpenAI()
OLLAMA_API = "http://localhost:11434/api/chat"
HEADERS = {"Content-Type": "application/json"}


##TODO create a tutor that helps you with questions
def ask_question(question) -> None:
    system_prompt = (
        "You are a tutor. Your job is to help a student with any question he asks you"
    )
    user_prompt = question
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    response = openai.chat.completions.create(model=MODEL, messages=messages)
    print(response.choices[0].message.content)
    print("The response from ollama is given below")
    response = ollama.chat(model="llama3.2", messages=messages)
    print(response["message"]["content"])


ask_question(
    """
Please explain what this code does and why:
yield from {book.get("author") for book in books if book.get("author")}
"""
)
