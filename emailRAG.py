import os
from dotenv import load_dotenv
import glob
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
import gradio as gr
from bs4 import BeautifulSoup
from langchain.memory import ConversationBufferMemory
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.schema import Document
from langchain.chains import ConversationalRetrievalChain
from langchain.embeddings import HuggingFaceBgeEmbeddings

# ? Imports required for accessing emails
import imaplib
import email

MODEL="gpt-4o-mini"

load_dotenv(override=True)
os.environ['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY")

try:
    embeddings = OpenAIEmbeddings()
    print("✅ Your API key has access to OpenAIEmbeddings")
except Exception as e:
    print(f"Some other error occured: {str(e)}")

# ~ Starting the process of extracting emails

mail = imaplib.IMAP4_SSL("imap.gmail.com")
mail.login("your-gmail-goes-here", "your-app-password-goes-here")
mail.select("inbox")

status, data = mail.search(None, "ALL")
email_ids = data[0].split()
vectorstore_path = "emails_vectorstore"
# ~ Create the helper function called extract_email_content to extract the contents of an email

def extract_email_content(message):
    """ 
    This function extracts the content of an email
     
    Args:
        message (email.message.Message): The email message object to extract content from.

    Returns:
        str: The extracted plain text content of the email.
    """
    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if "attachment" in content_disposition:
                continue
            else:
                if content_type == "text/plain": # ? return the content if its just plain text
                    return part.get_payload(decode=True).decode(errors="ignore")
                elif content_type == "text/html":
                    # ^ extract the text from the html using BeautifulSoup
                    html = part.get_payload(decode=True).decode(errors="ignore")
                    soup = BeautifulSoup(html, "html.parser")
                    return soup.get_text()
    else:
        content_type = message.get_content_type()
        body = message.get_payload(decode=True).decode(errors="ignore")
        if content_type == "text/plain":
            return body
        elif content_type == "text/html":
            soup = BeautifulSoup(body, "html.parser")
            return soup.get_text()
    return ""

email_ids = email_ids[-250:] # * Gets latest 250 emails because my account has about 5000 emails and 250 emails should be enough for this project
documents = []
for id in email_ids:
    status, data = mail.fetch(id, "(RFC822)")
    msg = email.message_from_bytes(data[0][1])
    content = extract_email_content(msg)
    if not content or not content.strip():
        continue
    if os.path.exists(vectorstore_path):
        print("📂 Loading existing vectorstore...")
        try:
            vectorstore = FAISS.load_local(
                vectorstore_path, 
                embeddings, 
                allow_dangerous_deserialization=True
            )
            print(f"✅ Vectorstore loaded successfully. It has {vectorstore.index.ntotal} embeddings")
            break
        except Exception as e:
            print(f"⚠️ Error loading vectorstore: {e}")
            print("🔄 Will create new vectorstore...")
    else:
        print("📚 Making a document object for an email")
        doc = Document(
            page_content=content,
            metadata={
                "email_id": id.decode(),
                "subject": msg.get("Subject", "No Subject"),
                "from": msg.get("From", "Unknown Sender"),
                "date": msg.get("Date", "Unknown Date"),
                "to": msg.get("To", "Unknown Recipient")
            }
        )
        documents.append(doc) 

# ? We do not need the mail connection anymore
mail.close()
mail.logout()

print(f"💻 Number of extracted emails : {len(documents)}") # ~ should display 250


batch_size = 50
if documents:
    if os.path.exists(vectorstore_path):
        print("📂 Loading existing vectorstore...")
        try:
            vectorstore = FAISS.load_local(
                vectorstore_path, 
                embeddings, 
                allow_dangerous_deserialization=True
            )
            print("✅ Vectorstore loaded successfully!")
        except Exception as e:
            print(f"⚠️ Error loading vectorstore: {e}")
            print("🔄 Will create new vectorstore...")
    else:
        first_batch = documents[:batch_size]
        vectorstore = FAISS.from_documents(first_batch, embeddings)
        print(f"✅ Created initial vectorstore with {len(first_batch)} documents")
        
        # Add remaining documents in batches
        for i in range(batch_size, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(documents) + batch_size - 1) // batch_size
            
            print(f"➕ Adding batch {batch_num}/{total_batches} ({len(batch)} documents)")
            
            try:
                # Create temporary vectorstore for this batch
                temp_vectorstore = FAISS.from_documents(batch, embeddings)
                # Merge with main vectorstore
                vectorstore.merge_from(temp_vectorstore)
                print(f"✅ Successfully added batch {batch_num}")
            except Exception as e:
                print(f"⚠️ Error processing batch {batch_num}: {str(e)}")
                continue
        vectorstore.save_local(vectorstore_path)
        print(f"🎉 Vectorstore created with {vectorstore.index.ntotal} total embeddings")
else:
    print("❗The documents list does not contain any emails")

# ? Setting up our LLM 

llm = ChatOpenAI(temperature=0.7, model_name=MODEL)

memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)

retriever = vectorstore.as_retriever()

conversation_chain = ConversationalRetrievalChain.from_llm(llm=llm, retriever=retriever, memory=memory)

# ? Now we need to create our gradio UI

def chat(message,history):
    response = conversation_chain.invoke({"question": message})
    return response["answer"]

view = gr.ChatInterface(chat, type="messages").launch(inbrowser=True)
