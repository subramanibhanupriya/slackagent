import os
import io  # Import io module
import pytest
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime
import requests

# Set environment variables for testing
os.environ['SLACK_BOT_TOKEN'] = "your-slack-bot-token"
os.environ['SLACK_APP_TOKEN'] = "your-slack-app-token"
os.environ['SLACK_CHANNEL_ID'] = "your-slack-channel-id"

def create_file(file_name="meeting_notes.txt", content="Sample meeting notes content."):
    """Create a sample file and upload it to Slack"""
    try:
        # Create a sample file
        with open(file_name, 'w') as f:
            f.write(content)
        
     # Set the Slack token and API endpoint
        slack_token = os.environ['SLACK_BOT_TOKEN']
        api_endpoint = "https://slack.com/api/files.upload"

        # Set the authentication headers
        headers = {
            "Authorization": f"Bearer {slack_token}",
            "Content-Type": "application/json"
        }

        # Upload the file to Slack
        response = requests.post(api_endpoint, headers=headers, files={"file": open(file_name, "rb")})

        # Check if the file was uploaded successfully
        if response.status_code == 200:
            response_json = response.json()
            if 'file' in response_json:
                print("Error uploading file:", response_json['file'])
                return None
            else:
                print("File uploaded successfully!")
                return response_json["file"]["id"]
        else:
            print(f"Error uploading file: {response.text}")
            return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None
        
def update_file(file_id, new_content="Updated meeting notes content."):
    """Update an existing file in Slack"""
    try:
        client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])
        
        # Update the file (Slack API does not allow direct file content updates, so we will re-upload)
        response = client.files_upload_v2(
            channel=os.environ['SLACK_CHANNEL_ID'],
            file=io.BytesIO(new_content.encode('utf-8')),
            filename="updated_meeting_notes.txt",
            title="Updated Meeting Notes",
            initial_comment="Here are the updated meeting notes."
        )
        
        print("File updated successfully!")
        print(f"Updated File ID: {response['file']['id']}")
    except SlackApiError as e:
        print(f"Error updating file: {e.response['error']}")
    except Exception as e:
        print(f"Error: {str(e)}")

def delete_file(file_id):
    """Delete a specific file from Slack"""
    try:
        client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])
        response = client.files_delete(file=file_id)
        print("File deleted successfully!")
    except SlackApiError as e:
        print(f"Error deleting file: {e.response['error']}")
    except Exception as e:
        print(f"Error: {str(e)}")

def test_create_file():
    file_id = create_file()
    assert file_id is not None, "File creation failed."

def test_update_file():
    file_id = create_file()
    assert file_id is not None, "File creation failed."
    update_file(file_id)
    # Add assertions to verify the update

def test_delete_file():
    file_id = create_file()
    assert file_id is not None, "File creation failed."
    delete_file(file_id)
    # Add assertions to verify the deletion

def main(file_name="meeting_notes.txt"):
    # Create a file and get its ID
    file_id = create_file(file_name=file_name)
    
    if file_id:
        # Update the file
        update_file(file_id)
        
        # Delete the file
        delete_file(file_id)

if __name__ == "__main__":
    main()
