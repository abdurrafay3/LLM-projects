import torch
from transformers import pipeline
from dotenv import load_dotenv
import os
from openai import OpenAI, AuthenticationError
import gradio as gr

"""
This program is for 
"""

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
    model="distil-whisper/distil-large-v3",
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    device=0 if torch.cuda.is_available() else "cpu",
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
        submit_btn = gr.Button("Submit audio + text")
    with gr.Row():
        audio_file = gr.Audio(label="Upload Audio", type="filepath")

    # ^ This will get both the audio from the microphone and the audio file that is uploaded
    def audio_transcription(audio_from_mic, audio_from_file, text_input, history):
        # ^ We need to process both the audio from the file and the microphone recording
        messages = [
            {"role": "system", "content": "You are a helpful assistant"}
        ] + history
        if text_input:
            messages.append({"role": "user", "content": text_input})
        if audio_from_mic is not None:
            audio_from_mic_result = pipeline(
                audio_from_mic,
                generate_kwargs={"max_new_tokens": 100, "language": "english"},
            )
            messages.append(
                {
                    "role": "user",
                    "content": f"Voice Instructions: {audio_from_mic_result['text']}",
                }
            )
        if audio_from_file is not None:
            audio_from_file_result = pipeline(
                audio_from_file,
                chunk_length_s=30,
                batch_size=8,
                generate_kwargs={"max_new_tokens": 300, "language": "english"},
            )
            messages.append(
                {
                    "role": "user",
                    "content": f"The audio file transcription is: {audio_from_file_result['text']}",
                }
            )
        response = openai.chat.completions.create(
            model="gpt-4o-mini", messages=messages
        )
        reply = response.choices[0].message.content
        messages.append({"role":"assistant", "content":reply})
        return messages

    def clear_input(message, history):
        history += [{"role": "user", "content": message}]
        return "", history

    input.submit(audio_transcription,
    inputs=[audio_input, audio_file, input, chatbot],
    outputs=chatbot
).then(
    lambda: "",  # Clear text input
    outputs=input
)

    submit_btn.click(
        audio_transcription,
        inputs=[audio_input, audio_file, input, chatbot],
        outputs=chatbot,
    )

# ^ We can also add another button for uploading audio files

# & this function gets the input from the gradio textbox, appends it to history then output the history to chatbot
# & then from chatbot it input that history into the chat function which responds with the reply and the reply is output into the chatbot which enables openAI to behave like it has memory
# ^ It also clears the input ⬇️
#  TODO add another gradio row where the user can insert an audio file 

ui.launch(inbrowser=True)


# ^ Test with a URL first (this should work)
