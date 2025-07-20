# imports

import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from IPython.display import Markdown, display
from openai import OpenAI

# If you get an error running this cell, then please head over to the troubleshooting notebook!

# Load environment variables in a file called .env

load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')

# Check the key

if not api_key:
    print("No API key was found - please head over to the troubleshooting notebook in this folder to identify & fix!")
elif not api_key.startswith("sk-proj-"):
    print("An API key was found, but it doesn't start sk-proj-; please check you're using the right key - see troubleshooting notebook")
elif api_key.strip() != api_key:
    print("An API key was found, but it looks like it might have space or tab characters at the start or end - please remove them - see troubleshooting notebook")
else:
    print("API key found and looks good so far!")

openai = OpenAI()
# A class to represent a Webpage
# If you're not familiar with Classes, check out the "Intermediate Python" notebook



# Some websites need you to use proper headers when fetching them:
headers = {
 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}  #This is a dictionary

class Website: #making a class called Website

    def __init__(self, url): #initialising Website
        """
        Create this Website object from the given url using the BeautifulSoup library
        """
        self.url = url
        response = requests.get(url, headers=headers) #requests.get is a function that accepts a url and many optional parameters, one of which is headers. The response variable holds the functions output
        soup = BeautifulSoup(response.content, 'html.parser') #BeautifulSoup, also a function, expects response.content which is probably a string and another string which tells it what parser to use
        self.title = soup.title.string if soup.title else "No title found" #soup.title now contains the title of the website if it exists then its gonna be assigned to self.title
        for irrelevant in soup.body(["script", "style", "img", "input"]): #using a for loop to iterate through soup.body(tags here) which means it looks for these tags and then the decompose function removes them
            irrelevant.decompose()
        self.text = soup.body.get_text(separator="\n", strip=True) #a function that extracts all text from the website and then separates different texts with a line and strips them

        # Define our system prompt - you can experiment with this later, changing the last sentence to 'Respond in markdown in Spanish."

system_prompt = "You are an assistant that analyzes the contents of a website \
and provides a short summary, ignoring text that might be navigation related. \
Respond in markdown."

# A function that writes a User Prompt that asks for summaries of websites:

def user_prompt_for(website):
    user_prompt = f"You are looking at a website titled {website.title}"
    user_prompt += "\nThe contents of this website is as follows; \
please provide a short summary of this website in markdown. \
If it includes news or announcements, then summarize these too.\n\n"
    user_prompt += website.text
    return user_prompt

messages = [
    {"role": "system", "content": "You are a snarky assistant"},
    {"role": "user", "content": "What is 2 + 2?"}
]

# See how this function creates exactly the format above

def messages_for(website):
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_for(website)}
    ]

# And now: call the OpenAI API. You will get very familiar with this!

def summarize(url):
    website = Website(url)
    response = openai.chat.completions.create(
        model = "gpt-4o-mini",
        messages = messages_for(website)
    )
    return response.choices[0].message.content

# A function to display this nicely in the Jupyter output, using markdown

def display_summary(url):
    summary = summarize(url)
    print(summary)

    display_summary("https://edwarddonner.com")