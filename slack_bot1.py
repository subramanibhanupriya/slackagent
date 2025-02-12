from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_drive_integration import fetch_notes_from_drive  # Import Drive function

slack_token = "your-slack-bot-token"
client = WebClient(token=slack_token)

def handle_slack_command(command, channel_id):
    if "fetch notes" in command:
        search_query = command.replace("fetch notes", "").strip()
        notes = fetch_notes_from_drive(search_query)  # Fetch from Drive

        try:
            client.chat_postMessage(channel=channel_id, text=notes)
        except SlackApiError as e:
            print(f"Error posting message: {e}")

    else:
        try:
            client.chat_postMessage(channel=channel_id, text="Invalid command.")
        except SlackApiError as e:
            print(f"Error posting message: {e}")