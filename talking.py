import os
from dotenv import load_dotenv
import ollama
from openai import OpenAI

load_dotenv(override=True)
openai_api_key = os.getenv("OPENAI_API_KEY")  # ^OpenAI API key
ollama_api_url = "http://localhost:11434"

openai = OpenAI()

gpt_messages = ["Hi there"]
ollama_messages = ["Hi"]


def call_gpt():  # *Setup GPT 4o Mini's response
    system_prompt = "You are a really rude person who always responds to everything in a snarky way. This makes you unlikeable by most but you can still form friendships"
    # * Creating the system prompt for chatGPT
    messages = [{"role": "system", "content": system_prompt}]

    # *passing in the response of ollama
    for gpt, ollama_msg in zip(gpt_messages, ollama_messages):
        messages.append({"role": "assistant", "content": gpt})
        messages.append({"role": "user", "content": ollama_msg})

    # *Getting GPT's response
    response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
    return response.choices[0].message.content


# ^ Creating the same function for ollama


def call_ollama() -> str:
    system_prompt = "You are a really kind person who is always calm. You try to find common ground when someone is being rude or snarky"
    messages = [{"role": "system", "content": system_prompt}]
    for gpt, ollama_msg in zip(gpt_messages, ollama_messages):
        messages.append({"role": "assistant", "content": ollama_msg})
        messages.append({"role": "user", "content": gpt})
    messages.append({"role": "user", "content": gpt_messages[-1]})
    response = ollama.chat(model="tinyllama", messages=messages)
    return response["message"]["content"]


# ^Now we cause more calls

print(f"GPT:\n{gpt_messages[0]}\n")
print(f"Ollama:\n{ollama_messages[0]}\n")

for i in range(5):
    gpt_next = call_gpt()
    gpt_messages.append(gpt_next)
    ollama_next = call_ollama()
    ollama_messages.append(ollama_next)
    print(f"GPT:\n{gpt_next}\n")
    print(f"Ollama:\n{ollama_next}\n")
