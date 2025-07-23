from openai import OpenAI
import json
import os
from dotenv import load_dotenv
import gradio as gr


load_dotenv(override=True)

get_api_key = os.getenv("OPENAI_API_KEY")

openai = OpenAI()


price_function = {
    "name": "get_ticket_prices",
    "description": "Call this tool whenever you want to know the price of a ticket to a destination city",
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {
                "type": "string",
                "description": "The city for which the ticket price is requested",
            },
        },
        "required": ["destination_city"],
        "additionalProperties": False,
    },
}

tools = [{"type": "function", "function": price_function}]


def chat(message, history):
    system_prompt = "You are a helpful assistant for an airline called FLightAI. Your job is to help people asking questions and call the relevant tools. If you do not know the answer, just say so"
    messages = (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": message}]
    )
    # *connect this to openai and stream the result
    response = openai.chat.completions.create(
        model="gpt-4o-mini", messages=messages, tools=tools
    )

    if response.choices[0].finish_reason == "tool_calls":
        # TODO call the handle_tool_call function to get
        message = response.choices[0].message
        response, destination_city = handle_tool_call(message)
        # TODO append the response to messages along with the last assitants message
        messages.append(message)
        messages.append(response)
        # TODO call openai again with the updated messages
        response = openai.chat.completions.create(
            model="gpt-4o-mini", messages=messages
        )
    return response.choices[0].message.content


def get_ticket_prices(city: str) -> str:
    ticket_prices = {
        "berlin": "$899",
        "tokyo": "$1400",
        "hong kong": "$1000",
        "london": "$699",
    }
    destination_city = city.lower()
    return ticket_prices.get(destination_city, "Unknown")


def handle_tool_call(message):
    # TODO grab the tool call from message
    tool_call = message.tool_calls[0]
    # TODO turn the tool_call from string to code
    arguments = json.loads(tool_call.function.arguments)
    # TODO get the argument for the function
    city = arguments.get("destination_city")
    ticket_price = get_ticket_prices(city)
    # TODO build up the json response manually
    response = {
        "role": "tool",
        "content": json.dumps({"destination_city": city, "price": ticket_price}),
        "tool_call_id": tool_call.id,
    }
    return response, city


gr.ChatInterface(fn=chat, type="messages").launch(share=True)
