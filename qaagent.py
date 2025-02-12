import os
import logging
import argparse
import google.auth
import google.auth.exceptions
from google.oauth2 import service_account
from googleapiclient.discovery import build
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.errors import SlackApiError
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, GoogleGenerativeAI
from langchain.chains import RetrievalQA
from dotenv import load_dotenv
from slack_sdk.rtm_v2 import RTMClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment Variables
SERVICE_ACCOUNT_FILE = os.path.abspath("credentials.json")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "#general")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE").split("#")[0].strip()

# Debugging prints for environment variables
print("Environment Variables Loaded:")
print(f"GOOGLE_SERVICE_ACCOUNT_FILE: {SERVICE_ACCOUNT_FILE}")  # Ensure no extra quotes or comments
print(f"SLACK_BOT_TOKEN: {SLACK_BOT_TOKEN}")  # Ensure no extra quotes or comments
print(f"SLACK_CHANNEL: {SLACK_CHANNEL}")
print(f"SLACK_APP_TOKEN: {SLACK_APP_TOKEN}")  # Ensure no extra quotes or comments




# Authenticate Google Drive
def authenticate_google_drive():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=credentials)

# Fetch text from a single Google Drive file
def load_documents_from_drive(file_id):
    drive_service = authenticate_google_drive()
    try:
        request = drive_service.files().get_media(fileId=file_id)
        file_content = request.execute()
        return file_content.decode("utf-8", errors="ignore")  # Assuming text file
    except Exception as e:
        print(f"❌ Error loading file {file_id}: {e}")
        return None

# Fetch all text files in a Google Drive folder
def load_documents_from_folder(folder_id):
    drive_service = authenticate_google_drive()
    try:
        query = f"'{folder_id}' in parents and mimeType='text/plain'"
        results = drive_service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get("files", [])

        if not files:
            return None

        documents = []
        for file in files:
            file_content = load_documents_from_drive(file["id"])
            if file_content:
                documents.append(file_content)

        return "\n".join(documents)  # Combine all file contents
    except Exception as e:
        print(f"❌ Error loading folder {folder_id}: {e}")
        return None

# Create embeddings using Google Generative AI
def create_embeddings():
    try:
        credentials, _ = google.auth.default()
        return GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    except google.auth.exceptions.DefaultCredentialsError:
        print("❌ No valid credentials found. Set up authentication first.")
        exit(1)

# Convert document(s) into a FAISS vector store
def create_vectorstore(document_text):
    if not document_text:
        print("❌ No document text provided for vectorstore")
        return None

    try:
        embeddings = create_embeddings()
        
        # Use a temporary file to store the document text
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as temp_file:
            temp_file.write(document_text)
            temp_file_path = temp_file.name

        # Load the document from the temporary file
        from langchain.docstore.document import Document
        doc_loader = TextLoader(temp_file_path)
        documents = doc_loader.load()

        # Create vectorstore
        vectorstore = FAISS.from_documents(documents, embeddings)
        
        # Clean up temporary file
        import os
        os.unlink(temp_file_path)
        
        return vectorstore
    except Exception as e:
        print(f"❌ Error creating vectorstore: {e}")
        return None

# Create QA chain
def create_qa_chain(vectorstore):
    return RetrievalQA.from_chain_type(
        llm=GoogleGenerativeAI(model="gemini-pro"),
        chain_type="stuff",
        retriever=vectorstore.as_retriever(),
    )

# Run the QA pipeline for file or folder
def run_qa_pipeline(source_id, question, is_folder=False):
    try:
        document_text = load_documents_from_folder(source_id) if is_folder else load_documents_from_drive(source_id)

        if not document_text:
            return "Error: Could not fetch document(s). Please check the file/folder ID."

        vectorstore = create_vectorstore(document_text)
        if not vectorstore:
            return "Error: Could not create vector store from documents."

        qa_chain = create_qa_chain(vectorstore)
        
        return qa_chain.run(question)

    except Exception as e:
        print(f"❌ QA Pipeline Error: {e}")
        return f"An unexpected error occurred: {str(e)}"

# Slack message handler
def handle_slack_message(client, event):
    try:
        # Extract message details
        data = event.get('event', {}) if 'event' in event else event
        user_text = data.get('text', '').strip()
        channel = data.get('channel')

        logger.info(f"Received message in channel {channel}: {user_text} | User text: {user_text}")

        # Your existing message handling logic
        if user_text.lower().startswith("/ask"):
            parts = user_text.split(" ", 2)
            if len(parts) < 3:
                send_slack_message(channel, "❌ Usage: `/ask <file_id> <question>`")
                return
            
            file_id, question = parts[1], parts[2]
            send_slack_message(channel, f"🔍 Searching document `{file_id}` for: *{question}* | User asked: {question}")

            # Get answer
            answer = run_qa_pipeline(file_id, question, is_folder=False)
            send_slack_message(channel, f"📝 *Answer:* {answer}")

        elif user_text.lower().startswith("/ask-folder"):
            parts = user_text.split(" ", 2)
            if len(parts) < 3:
                send_slack_message(channel, "❌ Usage: `/ask-folder <folder_id> <question>`")
                return
            
            folder_id, question = parts[1], parts[2]
            send_slack_message(channel, f"📂 Searching folder `{folder_id}` for: *{question}*")

            # Get answer
            answer = run_qa_pipeline(folder_id, question, is_folder=True)
            send_slack_message(channel, f"📄 *Answer from folder:* {answer}")

    except Exception as e:
        logger.error(f"Error handling Slack message: {e}")

# Socket Mode message handler
def socket_handler(client: SocketModeClient, req):
    if req.type == "events_api":
        # Acknowledge the request
        response = SocketModeResponse(envelope_id=req.envelope_id)
        client.send_socket_mode_response(response)
        
        # Process the event
        handle_slack_message(client, req.payload)

# RTM message handler
def rtm_handler(client, event):
    handle_slack_message(client, event)

# Send Slack message function
def send_slack_message(channel, text):
    try:
        client = WebClient(token=SLACK_BOT_TOKEN)
        response = client.chat_postMessage(channel=channel, text=text)
        logger.info(f"Message sent: {response['ts']}")
    except SlackApiError as e:
        logger.error(f"Slack API Error: {e.response['error']}")

# Slack bot starter function
def start_slack_bot(use_socket_mode=True):
    try:
        # Initialize Slack client
        slack_token = os.getenv("SLACK_BOT_TOKEN")
        slack_app_token = os.getenv("SLACK_APP_TOKEN")  # Optional for Socket Mode

        if not slack_token:
            logger.error("No Slack Bot Token found. Please set SLACK_BOT_TOKEN.")
            return

        if use_socket_mode:
            if not slack_app_token:
                logger.warning("No Slack App Token found. Falling back to RTM Mode.")
                use_socket_mode = False
            else:
                logger.info("Starting Slack bot in Socket Mode...")
                socket_client = SocketModeClient(
                    app_token=slack_app_token,
                    web_client=WebClient(token=slack_token)
                )
                
                # Register socket mode handler
                socket_client.socket_mode_request_listeners.append(socket_handler)
                socket_client.connect()
        else:
            logger.info("Starting Slack bot in RTM Mode...")
            rtm_client = RTMClient(token=slack_token)
            rtm_client.on(event="message")(rtm_handler)
            rtm_client.connect()

    except Exception as e:
        logger.error(f"Error starting Slack bot: {e}")

# Main function to start the Slack bot
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Slack Bot for Document Management")
    
    # Make document_id optional with a default value
    parser.add_argument("document_id", nargs='?', default=None, 
                        help="Optional document ID to load (for future use)")

    # Add an optional flag to start in bot mode
    parser.add_argument("--bot", action="store_true", 
                        help="Start Slack bot in Socket Mode")

    # Add an optional question argument for terminal input
    parser.add_argument("--question", type=str, 
                        help="Question to ask the document")

    args = parser.parse_args()

    try:
        # If --bot flag is set or no specific action is provided
        if args.bot or args.document_id is None:
            print("🚀 Starting Slack Document QA Bot...")
            
            # Prefer Socket Mode, fallback to RTM
            start_slack_bot(use_socket_mode=True)
        
        # If a document_id and question are provided, process the question
        elif args.document_id and args.question:
            print(f"Processing document: {args.document_id} with question: {args.question}")
            answer = run_qa_pipeline(args.document_id, args.question)
            print(f"📝 *Answer:* {answer}")

    except Exception as e:
        print(f"❌ Error starting application: {e}")
