import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import pypdf
import docx

client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])

def handle_file_query(file_name):
    file_path = f"./{file_name}"  # Adjust the path as necessary
    if os.path.exists(file_path):
        if file_name.endswith('.pdf'):
            return extract_text_from_pdf(file_path)
        elif file_name.endswith('.docx'):
            return extract_text_from_docx(file_path)
        else:
            with open(file_path, 'r') as file:
                return file.read()
    else:
        return f"Error: The file '{file_name}' does not exist."

def extract_text_from_pdf(file_path):
    with open(file_path, 'rb') as file:
        reader = pypdf.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text
