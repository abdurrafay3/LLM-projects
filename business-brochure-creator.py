import os 
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import requests
import json
from typing import List
from openai import OpenAI
from IPython.display import Markdown, display, update_display


# Define default headers for HTTP requests
load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')

if api_key and api_key.startswith('sk-proj-') and len(api_key)>10:
    print("API key looks good so far")
else:
    print("There might be a problem with your API key? Please visit the troubleshooting notebook!")
    
MODEL = 'gpt-4o-mini'
openai = OpenAI()
headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
}

class Website:
    def __init__(self,url):
        self.url = url
        response = requests.get(url, headers=headers)
        self.body = response.content
        soup = BeautifulSoup(self.body, 'html.parser')
        self.title = soup.title.string if soup.title else "No Title found"
        if soup.body:
            for irrelevant in soup.body(["script", "img", "style", "input"]):
                irrelevant.decompose()
            self.text = soup.body.get_text(separator = "\n", strip=True)
        else:
            soup.text = ""
        self.links = [link.get('href') for link in soup.find_all('a') if soup.find_all('a')]
    def get_content (self):
        return f"Webpage Title: {self.title}\n Webpage Content: {self.text} \n Website Links: {self.links}"

def find_relevant_links(url) -> str:
    website = Website(url)
    system_prompt = "You will be given a website, its title, its content and its links. Filter out the relevant links which can be used to make a business brochure for that website. Please give you response in a JSON file format and replace links such as /about with https://www.companyname/about"
    system_prompt+= "Your JSON file should have this format without ```json"
    system_prompt += """
{
    "links": [
        {"type": "about page", "url": "https://full.url/goes/here/about"},
        {"type": "careers page": "url": "https://another.full.url/careers"}
    ]
}
"""
    user_prompt = f"I am giving you a website with title,{website.title}, its content is, {website.text} and its links are {website.links}. Please find the relevant links required to make a business brochure for this website/company. Also, use the links for the socials in the social section of the brochure."
    messages = [
        {"role": "system", "content" : system_prompt},
        {"role": "user", "content" : user_prompt}
    ]
    response = openai.chat.completions.create(model="gpt-4o-mini", messages = messages)
    relevant_list = response.choices[0].message.content
    return relevant_list


relevant_list = find_relevant_links("https://huggingface.co")
parsed_relevant_links = json.loads(relevant_list)
website = Website("https://huggingface.co")
user_prompt = f"I am giving a website with title {website.title}, its content, {website.text} and the content of its relevant links is: "
for link in parsed_relevant_links["links"]:
    if link.get("url").startswith(("https://, https:\\")):
        website = Website(link.get("url"))
        user_prompt += website.text
user_prompt += "Make a business brochure for this website using all this content"
user_prompt = user_prompt[:5000]
messages = [
    {"role":"user","content":user_prompt},
    {"role":"system", "content":"You are an assistant that analyzes the contents of several relevant pages from a company website \
and creates a short brochure about the company for prospective customers, investors and recruits. Respond in markdown.\
Include details of company culture, customers and careers/jobs if you have the information."}
]
response = openai.chat.completions.create(model="gpt-4o-mini", messages = messages)
business_brochure = response.choices[0].message.content
print(business_brochure)
