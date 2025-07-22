import os
from dotenv import load_dotenv
import ollama
from openai import OpenAI
import gradio as gr

load_dotenv(override=True)
get_api_key = os.getenv("OPENAI_API_KEY")
openai = OpenAI()

system_prompt = "You are a helpful assistant that tries to answer every question the best you can. If you do not know the answer, you are honest and can say that you do not know"


def chat(message, history):
    messages = (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": message}]
    )

    stream = openai.chat.completions.create(
        model="gpt-4o-mini", messages=messages, stream=True
    )
    response = ""
    for chunk in stream:
        response += chunk.choices[0].delta.content or ""
        yield response


gr.ChatInterface(fn=chat, type="messages").launch(share=True)
