import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime
import tempfile
from langchain import OpenAI, LLMChain
import pypdf
import docx
from googleapiclient.http import MediaIoBaseDownload

class SlackFolderManager:
    def __init__(self, drive_service):
        # Initialize the Slack client
        self.client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])
        self.drive_service = drive_service

    def handle_file_query(self, file_path, action=None, content=None):
        # Logic to read the file and return answers using Langchain
        try:
            if action == "fetch":
                return self.fetch_note_content(file_path)
            elif action == "update":
                return self.update_note_content(file_path, content)
            elif action == "delete":
                return self.delete_note_content(file_path)
            else:
                return "Invalid action specified."

        except Exception as e:
            return f"Error processing file: {str(e)}"

    def fetch_note_content(self, file_path):
        if file_path.endswith('.pdf'):
            return self.extract_text_from_pdf(file_path)
        elif file_path.endswith('.docx'):
            return self.extract_text_from_docx(file_path)
        else:
            with open(file_path, 'r') as file:
                return file.read()

    def update_note_content(self, file_path, content):
        with open(file_path, 'w') as file:
            file.write(content)
        return "Note updated successfully."

    def delete_note_content(self, file_path):
        if os.path.exists(file_path):
            os.remove(file_path)
            return "Note deleted successfully."
        else:
            return "File not found."

    def extract_text_from_pdf(self, file_path):
        # Logic to extract text from PDF
        with open(file_path, 'rb') as file:
            reader = pypdf.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text

    def extract_text_from_docx(self, file_path):
        # Logic to extract text from DOCX
        doc = docx.Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text

    def process_drive_file(self, file_path):
        """Process a file fetched from Google Drive."""
        return self.handle_file_query(file_path)

    def fetch_and_process_note(self, file_id):
        """Fetch a note from Google Drive and process it."""
        request = self.drive_service.files().get_media(fileId=file_id)
        file_path = f"downloads/{file_id}"  # Define a path to save the file
        with open(file_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
        
        return self.handle_file_query(file_path)

    def upload_file_to_slack(self, file_path, channel_id):
        """Upload a file to Slack."""
        try:
            with open(file_path, "rb") as file_content:
                response = self.client.files_upload(
                    channels=channel_id,
                    file=file_content,
                    filename=os.path.basename(file_path)
                )
            return f"File '{os.path.basename(file_path)}' uploaded to Slack successfully. File ID: {response['file']['id']}"
        except SlackApiError as e:
            return f"Error uploading file to Slack: {e.response['error']}"
