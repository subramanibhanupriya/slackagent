import os
import datetime
import io
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from fpdf import FPDF
from docx import Document


# 🔹 Set API Keys
SLACK_TOKEN = "xoxb-8119294693044-8119319000436-tBpOkSPPdF97pFd3a9Zbtnqt"  # Replace with your Slack Bot Token
SLACK_CHANNEL = "C08CDEQEXA7"  # Change to your Slack channel
SERVICE_ACCOUNT_FILE = "venv/credentials.json"  # Path to Google Drive credentials JSON
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# ✅ Initialize Slack Client
slack_client = WebClient(token=SLACK_TOKEN)

# ✅ Authenticate Google Drive
def authenticate_google_drive():
    """Authenticate and return Google Drive API service."""
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

# ✅ Create a File and Upload to Google Drive
def create_and_upload_file(file_name, content, destination, file_format):
    """Creates a file, uploads to the chosen destination, and logs success messages."""
    temp_file_path = os.path.join(os.getcwd(), f"{file_name}.{file_format}")
    
    # Notify creation in terminal
    print(f"📄 Creating file '{file_name}.{file_format}'...")


    """Creates a file, uploads to the chosen destination, and logs success messages."""
    temp_file_path = os.path.join(os.getcwd(), f"{file_name}.{file_format}")

    # 🔹 Create the File Locally
    if file_format == "pdf":
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, content)
        pdf.output(temp_file_path)
    elif file_format == "docx":
        doc = Document()
        doc.add_paragraph(content)
        doc.save(temp_file_path)
    else:
        with open(temp_file_path, "w") as file:
            file.write(content)

    # 🔹 Upload to Google Drive Folder
    if destination == "drive":
        upload_file_to_drive(file_name, temp_file_path, "1aIlcLpvsyAs1GB-nIv5j5jVS0l3LV_2B", file_format)

    # Notify successful creation
    print(f"✅ File '{file_name}.{file_format}' created successfully.")
    send_slack_message(f"✅ File '{file_name}.{file_format}' created successfully on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.")

    return temp_file_path


# ✅ Upload File to Google Drive
def upload_file_to_drive(file_name, file_path, folder_id, file_format):
    """Uploads a file to Google Drive and logs success messages."""
    drive_service = authenticate_google_drive()
    if file_format == "pdf":
        media = MediaFileUpload(file_path, mimetype='application/pdf')
    elif file_format == "docx":
        media = MediaFileUpload(file_path, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    else:
        media = MediaFileUpload(file_path, mimetype='text/plain')

    file_metadata = {
        'name': file_name,
        'parents': [folder_id]  # Specify the folder ID here
    }

    try:
        print(f"🔄 Uploading '{file_name}' to Google Drive...")
        file = drive_service.files().create(body=file_metadata, media_body=media, fields='id, createdTime').execute()
        file_id = file['id']
        created_time = file['createdTime']

        # Convert UTC time to readable format
        readable_time = datetime.datetime.fromisoformat(created_time.replace("Z", "+00:00")).strftime('%Y-%m-%d %H:%M:%S')

        print(f"✅ File '{file_name}' uploaded successfully with ID: {file_id} and format: {file_format}")

        return file_id
    except Exception as e:
        print(f"❌ Error uploading file: {e}")
        return None

# ✅ Fetch File from Google Drive and Upload to Slack
def fetch_file_from_drive_and_upload(file_id):
    """Fetches a file from Google Drive using its ID and uploads it to Slack."""
    drive_service = authenticate_google_drive()
    
    try:
        # 🔹 Get File Metadata (Name)
        file = drive_service.files().get(fileId=file_id, fields="name").execute()
        file_name = file['name']
        
        # 🔹 Request File Data
        request = drive_service.files().get_media(fileId=file_id)

        # 🔹 Save File Locally
        temp_file_path = os.path.join(os.getcwd(), file_name)
        with open(temp_file_path, "wb") as f:
            f.write(request.execute())

        # 🔹 Upload to Slack
        upload_file_to_slack(file_name, temp_file_path)

        # 🔹 Delete Temporary File After Upload
        os.remove(temp_file_path)
        print(f"✅ Successfully fetched '{file_name}' from Google Drive and uploaded to Slack.")
        send_slack_message(f"✅ Successfully fetched '{file_name}' from Google Drive and uploaded to Slack. 🎉")

    except Exception as e:
        print(f"❌ Error fetching file from Drive: {e}")

# ✅ Upload File to Slack
def upload_file_to_slack(file_name, file_path):
    """Uploads a file to Slack."""
    try:
        with open(file_path, "rb") as file_content:
            slack_client.files_upload_v2(
                channels=SLACK_CHANNEL,
                file=file_content,
                filename=file_name
            )
        print(f"✅ File '{file_name}' uploaded to Slack successfully!")
        send_slack_message(f"✅ *File '{file_name}' uploaded to Slack!* 🎉")
    except SlackApiError as e:
        print(f"❌ Error uploading to Slack: {e.response['error']}")
        send_slack_message(f"❌ Error uploading to Slack: {e.response['error']}")

# ✅ List Files in Google Drive
def list_files_in_drive():
    """Lists all files stored in Google Drive."""
    drive_service = authenticate_google_drive()
    results = drive_service.files().list(fields="files(id, name)").execute()
    files = results.get('files', [])

    if not files:
        print("📂 No files found in Google Drive.")
        send_slack_message("📂 No files found in Google Drive.")
        return

    file_list = "\n".join([f"📄 `{file['name']}` (ID: `{file['id']}`)" for file in files])
    print(f"📂 *Files in Google Drive:*\n{file_list}")
    send_slack_message(f"📂 *Files in Google Drive:*\n{file_list}")

# ✅ Send Slack Notification
def send_slack_message(message):
    """Send a message to Slack."""
    try:
        slack_client.chat_postMessage(channel=SLACK_CHANNEL, text=message)
    except SlackApiError as e:
        print(f"❌ Slack API Error: {e.response['error']}")

def list_files_in_slack():
    """Lists all files stored in Slack."""
    try:
        response = slack_client.files_list(channel=SLACK_CHANNEL)
        files = response['files']
        if not files:
            print("📂 No files found in Slack.")
            send_slack_message("📂 No files found in Slack.")
            return

        file_list = "\n".join([f"📄 `{file['name']}` (ID: `{file['id']}`)" for file in files])
        print(f"📂 *Files in Slack:*\n{file_list}")
        send_slack_message(f"📂 *Files in Slack:*\n{file_list}")
    except SlackApiError as e:
        print(f"❌ Error listing files in Slack: {e.response['error']}")

# ✅ Rename File Function
def rename_file(current_name, new_name):
    """Renames a file in Google Drive or Slack."""
    drive_service = authenticate_google_drive()
    
    # Implement renaming logic for Google Drive
    file_id = None
    results = drive_service.files().list(q=f"name='{current_name}'", fields="files(id)").execute()
    items = results.get('files', [])
    if items:
        file_id = items[0]['id']
        drive_service.files().update(fileId=file_id, body={'name': new_name}).execute()
        print(f"✅ File renamed from '{current_name}' to '{new_name}' in Google Drive.")
    else:
        print(f"❌ File '{current_name}' not found in Google Drive.")

def update_file_content(file_name, new_content):
    """Updates the content of a file in Google Drive or Slack."""
    drive_service = authenticate_google_drive()
    
    # Implement updating logic for Google Drive
    file_id = None
    results = drive_service.files().list(q=f"name='{file_name}'", fields="files(id)").execute()
    items = results.get('files', [])
    if items:
        file_id = items[0]['id']
        media = MediaFileUpload(io.BytesIO(new_content.encode()), mimetype='text/plain')
        drive_service.files().update(fileId=file_id, media_body=media).execute()
        print(f"✅ File '{file_name}' updated in Google Drive.")
    else:
        print(f"❌ File '{file_name}' not found in Google Drive.")

# ✅ Delete File Function
def delete_file(file_name):
    """Deletes a file from Google Drive or Slack."""
    drive_service = authenticate_google_drive()
    
    # Logic to delete the file from Google Drive
    file_id = None
    results = drive_service.files().list(q=f"name='{file_name}'", fields="files(id)").execute()
    items = results.get('files', [])
    if items:
        file_id = items[0]['id']
        drive_service.files().delete(fileId=file_id).execute()
        print(f"✅ File '{file_name}' deleted from Google Drive.")
    else:
        print(f"❌ File '{file_name}' not found in Google Drive.")

# ✅ User Menu
def main():
    while True:
        print("\n💡 Available Commands: create, fetch, update, list, rename, delete, help, exit")
        command = input("🔹 Enter a command: ").lower()
        
        if command == 'delete':
            file_name = input("🔄 Enter the file name to delete: ")
            delete_file(file_name)

        elif command == 'list':
            list_source = input("📂 List files from (slack/drive): ").lower()
            if list_source == "drive":
                list_files_in_drive()
            elif list_source == "slack":
                list_files_in_slack()
            else:
                print("❌ Invalid source. Please choose 'slack' or 'drive'.")

        elif command == 'rename':
            current_name = input("🔄 Enter the current file name: ")
            new_name = input("🔄 Enter the new file name: ")
            rename_file(current_name, new_name)

        elif command == 'update':
            file_name = input("🔄 Enter the file name to update: ")
            new_content = input("✍️ Enter the new content: ")
            update_file_content(file_name, new_content)

        elif command == 'create':
            file_name = input("📄 Enter file name: ")
            content = input("✍️ Enter file content: ")
            destination = input("🌍 Upload to? (slack/drive): ").lower()
            file_format = input("📄 Enter file format (pdf/docx/txt): ").lower()
            create_and_upload_file(file_name, content, destination, file_format)

        elif command == 'fetch':

            file_id = input("🔎 Enter Google Drive File ID to fetch and upload to Slack: ")
            fetch_file_from_drive_and_upload(file_id)

        elif command == 'exit':
            print("👋 Goodbye!")
            break

        else:
            print("❌ Invalid command. Try again. Available commands: create, fetch, update, list, rename, delete, help, exit.")

if __name__ == "__main__":
    main()
