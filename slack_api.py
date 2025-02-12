import logging
from typing import Dict, Optional, List, Callable
from datetime import datetime
import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

logger = logging.getLogger(__name__)

# Set logging level to DEBUG
logging.basicConfig(level=logging.DEBUG)

class SlackEventHandler:
    def __init__(self):
        self.message_created_handlers: List[Callable] = []
        self.message_updated_handlers: List[Callable] = []
        self.channel_created_handlers: List[Callable] = []
        self.channel_updated_handlers: List[Callable] = []
        
    def on_message_created(self, handler: Callable):
        self.message_created_handlers.append(handler)
        
    def on_message_updated(self, handler: Callable):
        self.message_updated_handlers.append(handler)
        
    def on_channel_created(self, handler: Callable):
        self.channel_created_handlers.append(handler)
        
    def on_channel_updated(self, handler: Callable):
        self.channel_updated_handlers.append(handler)
        
    def trigger_message_created(self, message_data: Dict):
        for handler in self.message_created_handlers:
            try:
                handler(message_data)
            except Exception as e:
                logger.error(f"Error in message_created handler: {str(e)}")

    def trigger_message_updated(self, message_data: Dict):
        for handler in self.message_updated_handlers:
            try:
                handler(message_data)
            except Exception as e:
                logger.error(f"Error in message_updated handler: {str(e)}")

class SlackAPI:
    def __init__(self, bot_token: str, app_token: str = None):
        """
        Initialize Slack API client
        :param bot_token: Slack Bot User OAuth Token
        :param app_token: Slack App-Level Token (for Socket Mode)
        """
        self.client = WebClient(token=bot_token)
        self.events = SlackEventHandler()
        if app_token:
            self.app = App(token=bot_token)
            self.socket_mode_handler = SocketModeHandler(self.app, app_token)

    def add_metadata(self, data: Dict) -> Dict:
        """Add metadata to the data dictionary"""
        data["metadata"] = {
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        return data

    def create_channel(self, name: str, is_private: bool = False, description: str = "") -> Dict:
        """
        Create a new channel in Slack
        :param name: Channel name
        :param is_private: Whether the channel should be private
        :param description: Channel description
        :return: Channel information
        """
        try:
            if is_private:
                response = self.client.conversations_create(
                    name=name,
                    is_private=True
                )
            else:
                response = self.client.conversations_create(
                    name=name,
                    is_private=False
                )
            
            if description:
                channel_id = response["channel"]["id"]
                self.client.conversations_set_topic(
                    channel=channel_id,
                    topic=description
                )
            
            return response["channel"]
        except SlackApiError as e:
            logger.error(f"Error creating channel: {e.response['error']}")
            raise

    def send_message(self, channel_id: str, text: str, thread_ts: Optional[str] = None) -> Dict:
        """
        Send a message to a channel
        :param channel_id: Channel ID
        :param text: Message text
        :param thread_ts: Thread timestamp to reply to
        :return: Message information
        """
        try:
            return self.client.chat_postMessage(
                channel=channel_id,
                text=text,
                thread_ts=thread_ts
            )
        except SlackApiError as e:
            logger.error(f"Error sending message: {e.response['error']}")
            raise

    def update_message(self, channel_id: str, message_ts: str, text: str) -> Dict:
        """
        Update an existing message
        :param channel_id: Channel ID
        :param message_ts: Message timestamp
        :param text: New message text
        :return: Updated message information
        """
        try:
            return self.client.chat_update(
                channel=channel_id,
                ts=message_ts,
                text=text
            )
        except SlackApiError as e:
            logger.error(f"Error updating message: {e.response['error']}")
            raise

    def delete_message(self, channel_id: str, message_ts: str) -> Dict:
        """
        Delete a message
        :param channel_id: Channel ID
        :param message_ts: Message timestamp
        :return: Response information
        """
        try:
            return self.client.chat_delete(
                channel=channel_id,
                ts=message_ts
            )
        except SlackApiError as e:
            logger.error(f"Error deleting message: {e.response['error']}")
            raise

    def get_channel_history(self, channel_id: str, limit: int = 100) -> List[Dict]:
        """
        Get message history from a channel
        :param channel_id: Channel ID
        :param limit: Maximum number of messages to return
        :return: List of messages
        """
        try:
            response = self.client.conversations_history(
                channel=channel_id,
                limit=limit
            )
            return response["messages"]
        except SlackApiError as e:
            logger.error(f"Error getting channel history: {e.response['error']}")
            raise

    def search_messages(self, query: str) -> List[Dict]:
        """
        Search for messages
        :param query: Search query
        :return: List of matching messages
        """
        try:
            response = self.client.search_messages(
                query=query
            )
            return response["messages"]["matches"]
        except SlackApiError as e:
            logger.error(f"Error searching messages: {e.response['error']}")
            raise

    def upload_file(self, file_path: str, channel_id: str, title: str = None, initial_comment: str = None) -> Dict:
        """
        Upload a file to Slack
        :param file_path: Path to the file to upload
        :param channel_id: Channel ID to upload the file to
        :param title: Title for the file (optional)
        :param initial_comment: Comment to add with the file (optional)
        :return: Response information
        """
        try:
            with open(file_path, 'rb') as file_content:
                response = self.client.files_upload(
                    channels=channel_id,
                    file=file_content,
                    title=title,
                    initial_comment=initial_comment
                )
            return response
        except SlackApiError as e:
            logger.error(f"Error uploading file: {e.response['error']}")
            raise
        except IOError as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            raise

    def create_folder(self, folder_name: str, description: str = None) -> Dict:
        """
        Create a new folder (channel) in Slack
        :param folder_name: Name for the folder (channel)
        :param description: Optional description for the folder
        :return: Created folder information
        """
        try:
            # Create a private channel as a folder
            response = self.client.conversations_create(
                name=folder_name,
                is_private=True
            )
            
            if description and response['ok']:
                channel_id = response['channel']['id']
                self.client.conversations_setTopic(
                    channel=channel_id,
                    topic=description
                )
            
            return response
        except SlackApiError as e:
            logger.error(f"Error creating folder: {e.response['error']}")
            raise

    def list_folders(self) -> List[Dict]:
        """
        List all folders (private channels) in the workspace
        :return: List of folder information
        """
        try:
            response = self.client.conversations_list(
                types="private_channel",
                exclude_archived=True
            )
            return response['channels']
        except SlackApiError as e:
            logger.error(f"Error listing folders: {e.response['error']}")
            raise

    def delete_folder(self, folder_id: str) -> Dict:
        """
        Delete a 'folder' (archive a private channel) in Slack
        :param folder_id: ID of the folder to delete
        :return: Response information
        """
        try:
            response = self.client.conversations_archive(
                channel=folder_id
            )
            return response
        except SlackApiError as e:
            logger.error(f"Error deleting folder: {e.response['error']}")
            raise

    def move_to_folder(self, file_id: str, folder_id: str) -> Dict:
        """
        'Move' a file to a folder by sharing it in the folder's channel
        :param file_id: ID of the file to move
        :param folder_id: ID of the destination folder (channel)
        :return: Response information
        """
        try:
            # Share the file to the folder channel
            response = self.client.files_share(
                file=file_id,
                channel=folder_id
            )
            return response
        except SlackApiError as e:
            logger.error(f"Error moving file to folder: {e.response['error']}")
            raise

    def start_socket_mode(self):
        """Start the Socket Mode handler if app_token was provided"""
        if hasattr(self, 'socket_mode_handler'):
            self.socket_mode_handler.start()
        else:
            raise ValueError("No app_token provided during initialization")

if __name__ == "__main__":
    # Test the API connection
    slack = SlackAPI("your_bot_token", "your_app_token")
    # Example usage:
    # channel = slack.create_channel("test-channel", description="Test channel")
    # message = slack.send_message(channel["id"], "Hello, World!")

</read_file>

Now, I will create the updated `slack_api.py` file with the logging level set to `DEBUG`. 
""""
<create_file>
<path>slack_api.py</path>
<content>
import logging
from typing import Dict, Optional, List, Callable
from datetime import datetime
import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# Set logging level to DEBUG
logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

class SlackEventHandler:
    def __init__(self):
        self.message_created_handlers: List[Callable] = []
        self.message_updated_handlers: List[Callable] = []
        self.channel_created_handlers: List[Callable] = []
        self.channel_updated_handlers: List[Callable] = []
        
    def on_message_created(self, handler: Callable):
        self.message_created_handlers.append(handler)
        
    def on_message_updated(self, handler: Callable):
        self.message_updated_handlers.append(handler)
        
    def on_channel_created(self, handler: Callable):
        self.channel_created_handlers.append(handler)
        
    def on_channel_updated(self, handler: Callable):
        self.channel_updated_handlers.append(handler)
        
    def trigger_message_created(self, message_data: Dict):
        for handler in self.message_created_handlers:
            try:
                handler(message_data)
            except Exception as e:
                logger.error(f"Error in message_created handler: {str(e)}")

    def trigger_message_updated(self, message_data: Dict):
        for handler in self.message_updated_handlers:
            try:
                handler(message_data)
            except Exception as e:
                logger.error(f"Error in message_updated handler: {str(e)}")

class SlackAPI:
    def __init__(self, bot_token: str, app_token: str = None):
        """
        Initialize Slack API client
        :param bot_token: Slack Bot User OAuth Token
        :param app_token: Slack App-Level Token (for Socket Mode)
        """
        self.client = WebClient(token=bot_token)
        self.events = SlackEventHandler()
        if app_token:
            self.app = App(token=bot_token)
            self.socket_mode_handler = SocketModeHandler(self.app, app_token)

    def add_metadata(self, data: Dict) -> Dict:
        """Add metadata to the data dictionary"""
        data["metadata"] = {
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        return data

    def create_channel(self, name: str, is_private: bool = False, description: str = "") -> Dict:
        """
        Create a new channel in Slack
        :param name: Channel name
        :param is_private: Whether the channel should be private
        :param description: Channel description
        :return: Channel information
        """
        try:
            if is_private:
                response = self.client.conversations_create(
                    name=name,
                    is_private=True
                )
            else:
                response = self.client.conversations_create(
                    name=name,
                    is_private=False
                )
            
            if description:
                channel_id = response["channel"]["id"]
                self.client.conversations_set_topic(
                    channel=channel_id,
                    topic=description
                )
            
            return response["channel"]
        except SlackApiError as e:
            logger.error(f"Error creating channel: {e.response['error']}")
            raise

    def send_message(self, channel_id: str, text: str, thread_ts: Optional[str] = None) -> Dict:
        """
        Send a message to a channel
        :param channel_id: Channel ID
        :param text: Message text
        :param thread_ts: Thread timestamp to reply to
        :return: Message information
        """
        try:
            return self.client.chat_postMessage(
                channel=channel_id,
                text=text,
                thread_ts=thread_ts
            )
        except SlackApiError as e:
            logger.error(f"Error sending message: {e.response['error']}")
            raise

    def update_message(self, channel_id: str, message_ts: str, text: str) -> Dict:
        """
        Update an existing message
        :param channel_id: Channel ID
        :param message_ts: Message timestamp
        :param text: New message text
        :return: Updated message information
        """
        try:
            return self.client.chat_update(
                channel=channel_id,
                ts=message_ts,
                text=text
            )
        except SlackApiError as e:
            logger.error(f"Error updating message: {e.response['error']}")
            raise

    def delete_message(self, channel_id: str, message_ts: str) -> Dict:
        """
        Delete a message
        :param channel_id: Channel ID
        :param message_ts: Message timestamp
        :return: Response information
        """
        try:
            return self.client.chat_delete(
                channel=channel_id,
                ts=message_ts
            )
        except SlackApiError as e:
            logger.error(f"Error deleting message: {e.response['error']}")
            raise

    def get_channel_history(self, channel_id: str, limit: int = 100) -> List[Dict]:
        """
        Get message history from a channel
        :param channel_id: Channel ID
        :param limit: Maximum number of messages to return
        :return: List of messages
        """
        try:
            response = self.client.conversations_history(
                channel=channel_id,
                limit=limit
            )
            return response["messages"]
        except SlackApiError as e:
            logger.error(f"Error getting channel history: {e.response['error']}")
            raise

    def search_messages(self, query: str) -> List[Dict]:
        """
        Search for messages
        :param query: Search query
        :return: List of matching messages
        """
        try:
            response = self.client.search_messages(
                query=query
            )
            return response["messages"]["matches"]
        except SlackApiError as e:
            logger.error(f"Error searching messages: {e.response['error']}")
            raise

    def upload_file(self, file_path: str, channel_id: str, title: str = None, initial_comment: str = None) -> Dict:
        """
        Upload a file to Slack
        :param file_path: Path to the file to upload
        :param channel_id: Channel ID to upload the file to
        :param title: Title for the file (optional)
        :param initial_comment: Comment to add with the file (optional)
        :return: Response information
        """
        try:
            with open(file_path, 'rb') as file_content:
                response = self.client.files_upload(
                    channels=channel_id,
                    file=file_content,
                    title=title,
                    initial_comment=initial_comment
                )
            return response
        except SlackApiError as e:
            logger.error(f"Error uploading file: {e.response['error']}")
            raise
        except IOError as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            raise

    def create_folder(self, folder_name: str, description: str = None) -> Dict:
        """
        Create a new folder (channel) in Slack
        :param folder_name: Name for the folder (channel)
        :param description: Optional description for the folder
        :return: Created folder information
        """
        try:
            # Create a private channel as a folder
            response = self.client.conversations_create(
                name=folder_name,
                is_private=True
            )
            
            if description and response['ok']:
                channel_id = response['channel']['id']
                self.client.conversations_setTopic(
                    channel=channel_id,
                    topic=description
                )
            
            return response
        except SlackApiError as e:
            logger.error(f"Error creating folder: {e.response['error']}")
            raise

    def list_folders(self) -> List[Dict]:
        """
        List all folders (private channels) in the workspace
        :return: List of folder information
        """
        try:
            response = self.client.conversations_list(
                types="private_channel",
                exclude_archived=True
            )
            return response['channels']
        except SlackApiError as e:
            logger.error(f"Error listing folders: {e.response['error']}")
            raise

    def delete_folder(self, folder_id: str) -> Dict:
        """
        Delete a 'folder' (archive a private channel) in Slack
        :param folder_id: ID of the folder to delete
        :return: Response information
        """
        try:
            response = self.client.conversations_archive(
                channel=folder_id
            )
            return response
        except SlackApiError as e:
            logger.error(f"Error deleting folder: {e.response['error']}")
            raise

    def move_to_folder(self, file_id: str, folder_id: str) -> Dict:
        """
        'Move' a file to a folder by sharing it in the folder's channel
        :param file_id: ID of the file to move
        :param folder_id: ID of the destination folder (channel)
        :return: Response information
        """
        try:
            # Share the file to the folder channel
            response = self.client.files_share(
                file=file_id,
                channel=folder_id
            )
            return response
        except SlackApiError as e:
            logger.error(f"Error moving file to folder: {e.response['error']}")
            raise

    def start_socket_mode(self):
        """Start the Socket Mode handler if app_token was provided"""
        if hasattr(self, 'socket_mode_handler'):
            self.socket_mode_handler.start()
        else:
            raise ValueError("No app_token provided during initialization")

if __name__ == "__main__":
    # Test the API connection
    slack = SlackAPI("your_bot_token", "your_app_token")
    # Example usage:
    # channel = slack.create_channel("test-channel", description="Test channel")
    # message = slack.send_message(channel["id"], "Hello, World!")
</create_file>

Now, I will proceed to create the updated `slack_api.py` file with the logging level set to `DEBUG`.
