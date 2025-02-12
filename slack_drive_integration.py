from googleapiclient.discovery import build
from google.oauth2 import service_account

# Authenticate with Google Drive API
SCOPES = ["https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_FILE = "credentials.json"  # Use your service account file

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

drive_service = build("drive", "v3", credentials=creds)

# Function to fetch notes from Google Drive
def fetch_notes_from_drive(query):
    results = drive_service.files().list(
        q=f"name contains '{query}'",  # Search for file with query keyword
        fields="files(id, name, mimeType)",
    ).execute()
    
    files = results.get("files", [])
    if not files:
        return "No notes found."

    notes_list = "\n".join([f"{file['name']} (ID: {file['id']})" for file in files])
    return f"Found notes:\n{notes_list}"

# Example: Fetching notes containing "meeting"
notes = fetch_notes_from_drive("meeting")
print(notes)
# Output: Found notes:
# meeting_notes_2022-01-01.txt (ID: 123456789)
# meeting_notes_2022-01-15.txts (ID: 987654321)