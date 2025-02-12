import os
from dotenv import load_dotenv
from folder_manager import FolderManager

def main():
    # Load environment variables
    load_dotenv()
    
    # Get Slack token from environment variables
    slack_token = os.getenv('SLACK_BOT_TOKEN')
    channel_id = os.getenv('SLACK_CHANNEL_ID')
    
    if not slack_token or not channel_id:
        print("Please set SLACK_BOT_TOKEN and SLACK_CHANNEL_ID in your .env file")
        return

    # Initialize folder manager
    folder_manager = FolderManager(slack_token)
    
    # File timestamp from the previous create operation
    file_ts = "1735226245.569959"  # This is the timestamp from our previous create operation
    
    # Update the file with a new name
    new_file_name = "important_notes_updated.txt"
    print(f"Updating file to '{new_file_name}'...")
    
    result = folder_manager.update_folder(channel_id, file_ts, new_file_name)
    
    if result:
        print(f"File updated successfully to '{new_file_name}'!")
        print(f"File timestamp remains: {file_ts}")
    else:
        print("Failed to update file")

if __name__ == "__main__":
    main()
