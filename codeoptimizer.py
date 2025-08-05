import os
from dotenv import load_dotenv
from openai import OpenAI, AuthenticationError, PermissionDeniedError
import gradio as gr
import json
import subprocess
import tempfile

load_dotenv(override=True)

get_api_key = os.getenv("OPENAI_API_KEY")

openai = OpenAI()

# TODO create the function which converts the code ✅
# TODO create the function which runs the python code ✅
# TODO create the function which runs the cpp code ✅
# TODO create the chat function ✅
# TODO create the gradio UI ✅
# TODO link all the buttons of the gradio UI to the appropriate function ✅

# ? We only need 3 functions which are
# ^ optimize_python OR convert_to_cpp ==> Basically converts the python code to cpp code and then creates a new file and writes the code there
# ^ chat function because we need the model to be an instruct type ==> enables the model to carry out conversations
# ^ handle_tool_calls because if we need the model to have memory and carry out conversations then code generation would be a separate tool

generate_code = {
    "name": "convert_to_cpp",
    "description": "Call this tool whenever the user wants you to convert python code to cpp code and optimize it.",
    "parameters": {
        "type": "object",
        "properties": {
            "python_code": {
                "type": "string",
                "description": "The python code that the user wants you to convert into cpp code and optimize",
            }
        },
    },
    "required": ["python_code"],
    "additionalProperties": False,
}

tools = [{"type": "function", "function": generate_code}]


def run_python_code(python_code):
    if not python_code.strip():
        return "No Python code to run"
    
    timed_code = f"""
import time
start = time.time()

{python_code}

end= time.time()
print(f"Execution time: {{end - start:.4f}}")
"""
    python_code = timed_code
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(python_code)
            f.flush()
            
            result = subprocess.run(['python', f.name], capture_output=True, text=True, timeout=50)
            os.unlink(f.name)
            
            if result.returncode == 0:
                return result.stdout
            else:
                return f"Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out"
    except Exception as e:
        return f"Error: {str(e)}"

def run_cpp_code(cpp_code):
    if not cpp_code.strip():
        return "No C++ code to run"
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as cpp_file:
            cpp_file.write(cpp_code)
            cpp_file.flush()
            
            exe_file = cpp_file.name.replace('.cpp', '.exe') if os.name == 'nt' else cpp_file.name.replace('.cpp', '')
            compile_result = subprocess.run(['g++', '-o', exe_file, cpp_file.name], capture_output=True, text=True)
            
            if compile_result.returncode != 0:
                os.unlink(cpp_file.name)
                return f"Compilation Error: {compile_result.stderr}"
            
            run_result = subprocess.run([exe_file], capture_output=True, text=True, timeout=50)
            
            os.unlink(cpp_file.name)
            if os.path.exists(exe_file):
                os.unlink(exe_file)
                
            if run_result.returncode == 0:
                return run_result.stdout
            else:
                return f"Runtime Error: {run_result.stderr}"
                
    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out"
    except Exception as e:
        return f"Error: {str(e)}"


def handle_tool_calls(tool_call) -> str:
    # ? Get the function arguments
    print("✅ handle_tool_calls was called")
    arguments = json.loads(tool_call.function.arguments)
    if tool_call.function.name == "convert_to_cpp":
        cpp_code = convert_to_cpp(arguments["python_code"])
        return cpp_code



def chat(history):
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that can also convert python code to cpp and optimize it",
        }
    ] + history
    response = openai.chat.completions.create(
        model="gpt-4o", messages=messages, tools=tools
    )
    # ^ check if the response has a tool call in its finih reasons
    if response.choices[0].finish_reason == "tool_calls":
        messages.append(response.choices[0].message)
        for call in response.choices[0].message.tool_calls:
            if call.function.name == "convert_to_cpp":
                cpp_code = handle_tool_calls(call)
                # ? append the response from the tool to messages
                messages.append(
                    {"role": "tool", "tool_call_id": call.id, "content": cpp_code}
                )
                # ~ Generate a new response if the tool is called because gpt needs to read the tool call
        response = openai.chat.completions.create(
            model="gpt-4o", messages=messages, tools=tools
        )
    reply = response.choices[0].message.content
    # ^ append the reply to history
    history.append({"role": "assistant", "content": reply})
    return history


def convert_to_cpp(python_code: str) -> str:
    print("📚 convert_to_cpp was called")
    messages = [
        {
            "role": "system",
            "content": "Do not include ```cpp at the start and ``` at the end. Your job is to convert python code into more time efficient C++ code. Return only the C++ code. Also measure how much time it would take to execute that code and output the time taken. Make sure to #include iomanip and other packages which would be required for the code to run properly",
        },
        {
            "role": "user",
            "content": f"Please convert this python code to C++ code \n {python_code}",
        }
    ]
    
    try:
        stream = openai.chat.completions.create(model="gpt-4o", messages=messages, stream=True)
        full_response = ""
        cleaned_start = False
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content is not None:
                full_response += content
            yield full_response.strip()
    except Exception as e:
        yield f"// Error converting code: {str(e)}"



with gr.Blocks() as ui:
    gr.Markdown("## Convert code from Python to C++")
    gr.Markdown(
        "This model can carry out conversations and it has memory. Leave the code boxes empty if you do not want to convert your code and just want to have a normal conversation. The LLM will add some code at the end to calculate the time it took to execute the code"
    )
    with gr.Row():
        with gr.Column(scale=1):
            chatbot = gr.Chatbot(label="Chat with our AI Assistant", type="messages")
            input_text = gr.Textbox(label="Enter your prompt here")
        input_python_code = gr.Code(
            language="python", label="Please enter your python code here", lines=20
        )
        output_cpp_code = gr.Code(language="cpp", label="Your code in C++", lines=20)
    with gr.Row():
        convert_code = gr.Button("Submit all inputs")
    with gr.Row():
        run_python = gr.Button("Run the python code you entered")
        run_cpp = gr.Button("Run the C++ code that was output by GPT")
    with gr.Row():
        python_output = gr.TextArea(label="Output of python code", lines=30)
        cpp_output = gr.TextArea(label="Output of C++ code", lines=30)

    def manage_input(message, history):
        history.append({"role": "user", "content": message})
        return "", history

    convert_code.click(
        convert_to_cpp, inputs=input_python_code, outputs=output_cpp_code
    )
    input_text.submit(
        manage_input, inputs=[input_text, chatbot], outputs=[input_text, chatbot]
    ).then(chat, inputs=chatbot, outputs=chatbot)
    input_text.submit(convert_to_cpp, inputs=input_python_code, outputs=output_cpp_code)
    run_python.click(run_python_code, inputs=input_python_code, outputs=python_output)
    run_cpp.click(run_cpp_code, inputs=output_cpp_code, outputs=cpp_output)

ui.launch(share=True)
