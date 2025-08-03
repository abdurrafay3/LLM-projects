import torch
from transformers import pipeline
from dotenv import load_dotenv
import os
from openai import OpenAI, AuthenticationError
import gradio as gr

load_dotenv(override=True)
get_api_key = os.getenv("OPENAI_API_KEY")

openai = OpenAI()

try:
    models = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"},
        ],
    )
    print("✅ API Key is valid")
except AuthenticationError:
    print("❌ API Key is not valid")
except Exception as e:
    print(f"Some other error occured: {e}")


pipeline = pipeline(
    task="automatic-speech-recognition",
    model="openai/whisper-medium",
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    device=0 if torch.cuda.is_available() else "cpu",
    max_new_tokens=400,
    return_timestamps=False,
)


# ^ The chat function which is responsible for adding memory to the chatbot
# * The parameter history represents all the older messages + the recent user message when he enters a message in the gradio UI
# TODO we will later link the gradio UI input to this function
def chat(history):
    messages = [{"role": "system", "content": "You are a helpful assistant"}] + history
    # & generate the response
    response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
    # & We need to add this response to history and pass it back to the gradio UI
    reply = response.choices[0].message.content
    history += [{"role": "assistant", "content": reply}]
    return history


# ! This function basically updated the history, now we can handle the input from the gradio UI


# ^ converting the audio to text using whisper then returning it to gpt-4o-mini


##TODO creating a gradio user interface using gr.Blocks
with gr.Blocks() as ui:
    with gr.Row():
        chatbot = gr.Chatbot(type="messages")
    with gr.Row():
        input = gr.Textbox(label="Chat with our AI Assistant")
    with gr.Row():
        audio_input = gr.Microphone(label="Speak to our AI assistant", type="filepath")
        submit_btn = gr.Button("Submit audio to get the response")
    with gr.Row():
        audio_file = gr.Audio(label="Upload Audio", type="filepath")
       
    def audio_transcription(audio_file_path):
        audio_transcription = pipeline(audio_file_path)
        text_from_audio = audio_transcription["text"]
        response = [{"role":"user", "content": text_from_audio}]
        return response
    
    def clear_input(message, history):
        history += [{"role": "user", "content": message}]
        return "", history

    input.submit(clear_input, inputs=[input, chatbot], outputs=[input, chatbot]).then(
        chat, inputs=[chatbot], outputs=[chatbot]
    )

    submit_btn.click(
        audio_transcription,
        inputs=audio_input,
        outputs=chatbot
    ).then(
        chat,
        inputs=chatbot,
        outputs=chatbot
    )


# & this function gets the input from the gradio textbox, appends it to history then output the history to chatbot
# & then from chatbot it input that history into the chat function which responds with the reply and the reply is output into the chatbot which enables openAI to behave like it has memory
# ^ It also clears the input ⬇️
# TODO add another gradio row where the user can insert an audio file

ui.launch(inbrowser=True)


# ^ Test with a URL first (this should work)
result = pipeline("denver_extract.mp3")
print("Result is ready")
print(result)
