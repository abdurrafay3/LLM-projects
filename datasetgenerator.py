import os
from dotenv import load_dotenv
from openai import OpenAI
import json
import gradio as gr

load_dotenv(override=True)

api_key = os.getenv("OPENAI_API_KEY")

openai = OpenAI()

try:
    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"},
    ]
    response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
    print("✅ API key is valid")
except Exception as e:
    print(f"❌ Another error occured: {e}")

data_generator = {
    "name": "test_data_generator",
    "description": "Use this tool whenever the user asks to generate test data of conversational logs between a user and an assistant",
    "parameters": {
        "type": "object",
        "properties": {
            "input_data": {
                "type": "string",
                "description": "The type of data that the user wants you to generate i.e. conversational logs, customer details for a bank etc",
            },
        },
        "required": ["input_data"],
        "additionalProperties": False
    },
}


# ^ Building the function for the tool. It will return a list of dictionaries containing the test data sets
def test_data_generator(type_of_data) -> list:
    print("‼️test_data_generator was called")
    system_prompt = f"""Generate a single test data example of the type: {type_of_data} and give your reply in a JSON format as defined below:
    {{
        "name":"Alex",
        "subscription":"No",
        "Married":"Yes"  
    }}
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"Please generate data sets about {type_of_data} and give me the response in a JSON format",
        },
    ]
    test_data = []
    for i in range(5):
        response = openai.chat.completions.create(
            model="gpt-4o-mini", messages=messages
        )
        content = response.choices[0].message.content.strip()
        # ^ Since add will be a json type dictionary
        try:            
            # Fix: Ensure content is a string and handle None
            if content is None:
                print(f"⚠️ None response for iteration {i}")
                continue
                
            content = str(content).strip()  # Convert to string and strip
            
            # Now safe to call .lower()
            if not content or content.lower() == 'null':
                print(f"⚠️ Empty or null response for iteration {i}")
                continue
            
            # Try to extract JSON if wrapped in code blocks
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            # Parse JSON
            parsed_data = json.loads(content)
            test_data.append(parsed_data)
            print("✅ Appending to test data successful")
        except Exception as e:
            print(f"❌ An error occured : {e}")
    return test_data


tools = [{"type": "function", "function": data_generator}]


def chat(history):
    messages = [{"role": "system", "content": "You are a helpful assistant"}] + history
    response = openai.chat.completions.create(
        model="gpt-4o-mini", messages=messages, tools=tools
    )
    if response.choices[0].finish_reason == "tool_calls":
        messages.append(response.choices[0].message)
        for call in response.choices[0].message.tool_calls:
            if call.function.name == "test_data_generator":
                test_data = handle_tool_calls(call)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(test_data),
                    }
                )
                # ~ test data here is in the form of python list of dictionaries
                # ~ Use json.dumps() to convert it into a string and append to history
            response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
      # ^ gpt-4o-mini reads the tool call here
    reply = response.choices[0].message.content
    history.append({"role": "assistant", "content": reply})
    return history

def handle_tool_calls(tool_call):
    arguments = json.loads(tool_call.function.arguments)
    if tool_call.function.name == "test_data_generator":
        return test_data_generator(arguments["input_data"])

# ^ Creating the gradio UI
with gr.Blocks() as ui:
    with gr.Row():
        chatbot = gr.Chatbot(label="Chat with our AI assistant", type="messages")
    with gr.Row():
        input = gr.Textbox(label="Enter your prompt here")

    def manage_input(message, history):
        history.append({"role": "user", "content": message})
        return "", history

    input.submit(manage_input, inputs=[input, chatbot], outputs=[input, chatbot]).then(
        chat, inputs=chatbot, outputs=chatbot
    )
ui.launch(share=True)


# * Creating the handle tool call function


# ^ Creating the chat function and also handling the tool calls
