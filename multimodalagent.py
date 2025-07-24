import os
from openai import OpenAI, PermissionDeniedError, AuthenticationError
import json
import gradio as gr
from dotenv import load_dotenv

# &Imports required for images shown below
import base64
from io import BytesIO
from PIL import Image

load_dotenv(override=True)
get_api_key = os.getenv("OPENAI_API_KEY")
openai = OpenAI()


# *Checking if API key works
try:
    openai.models.retrieve("gpt-4o-mini")
    print("✅API Key works!")
except AuthenticationError:
    print("Invalid API key")
except PermissionDeniedError:
    print("🚫 API key is valid but lacks permission (missing scopes).")
except Exception as e:
    print(f"Other error: {e}")
try:
    openai.images.generate(
        model="dall-e-3",
        prompt="A futuristic robot in New York city with a vibrant pop out art style",
        size="1024x1024",
        n=1,
        response_format="url",
    )
    print("Image generation is allowed")
except PermissionDeniedError:
    print(" 🚫 API Key is valid but it cannot generate images")
except AuthenticationError:
    print("Invalid API Key")
except Exception as e:
    print(f"Other errors: {e}")

try:
    openai.audio.speech.create(
        model="tts-1", voice="onyx", input="This is a test of audio generation"
    )
    print("Audio generation is allowed")

except PermissionDeniedError:
    print("🚫 API Key is valid but it cannot generate audio")
except AuthenticationError:
    print("Invalid API Key")
except Exception as e:
    print(f"Other errors: {e}")

# * API key checks done

# TODO create the json list for the image tool
image_function = {
    "name": "get_image",
    "description": "Call this whenever the user wants to generate images",
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "This is the description of the image the user wants to create",
            }
        },
    },
    "required": ["prompt"],
    "additionalProperties": False,
}


# TODO create the function for getting the image
def get_image(prompt):
    print(f"🎨 get_image function ran with prompt: '{prompt}'")
    
    
    # image_response = openai.images.generate(
    #     model="dall-e-3",
    #     prompt=prompt,
    #     size="1024x1024",
    #     n=1,
    #     response_format="b64_json",
    # )
    # image_base64 = image_response.data[0].b64_json
    # image_data = base64.b64decode(image_base64)
    # return Image.open(BytesIO(image_data))
    
    # For testing: create a placeholder image
    img = Image.new('RGB', (400, 400), color='lightgreen')
    return img

def handle_tool_call(tool_call):
    print("get_handle_tool was called ")
    arguments = json.loads(tool_call.function.arguments)
    if tool_call.function.name == "get_image":
        return get_image(arguments["prompt"])
    return "Unknown tool"


tools = [{"type": "function", "function": image_function}]


def chat(history):
    messages = [{"role": "system", "content": "You are a helpful assistant"}] + history
    response = openai.chat.completions.create(
        model="gpt-4o-mini", messages=messages, tools=tools
    )
    image = None
    if response.choices[0].finish_reason == "tool_calls":
        messages.append(response.choices[0].message)
        for call in response.choices[0].message.tool_calls:
            if call.function.name == "get_image":
                image = handle_tool_call(call)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": "Image was generated successfully",
                    }
                )
        #*AI needs to respond that it generated the image
        response = openai.chat.completions.create(
            model="gpt-4o-mini", messages=messages, tools=tools
        )
    #*If no tools required, reply normally
    reply = response.choices[0].message.content
    history += [{"role": "assistant", "content": reply}]

    return history, image  # *No error if no image


# TODO Gradio UI

with gr.Blocks() as ui:
    with gr.Row():  # ^Defining the first row, containing 2 columns
        chatbot = gr.Chatbot(height=500, type="messages")
        imageOutput = gr.Image(height=500)
    with gr.Row():  # ^Second row textbox
        entry = gr.Textbox(label="Chat with our AI Assistant:")
    with gr.Row():
        clearButton = gr.Button("Clear")

    # *Managing submissions (means linking buttons to methods)
    def do_entry(message, history):
        history += [{"role": "user", "content": message}]
        return "", history

    entry.submit(do_entry, inputs=[entry, chatbot], outputs=[entry, chatbot]).then(
        chat, inputs=chatbot, outputs=[chatbot, imageOutput]
    )
    clearButton.click(lambda: None, inputs=None, outputs=chatbot, queue=False)

ui.launch(inbrowser=True)
