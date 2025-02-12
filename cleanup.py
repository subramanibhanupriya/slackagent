import os
import logging
from dotenv import load_dotenv
from note_manager import NoteManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Load environment variables
    load_dotenv()
    
    # Get API key from environment
    slack_api_key = os.getenv('SLACK_API_KEY')
    
    if not slack_api_key:
        logger.error("Missing SLACK_API_KEY environment variable")
        return

    try:
        # Initialize note manager
        note_manager = NoteManager(slack_api_key)
        
        # Search for test notes
        results = note_manager.search_notes("Introduction to Machine Learning")
        
        # Delete found notes
        for note in results:
            note_id = note.get('id')
            if note_id:
                logger.info(f"Deleting note {note_id}...")
                try:
                    note_manager.delete_note(note_id)
                    logger.info(f"Successfully deleted note {note_id}")
                except Exception as e:
                    logger.error(f"Error deleting note {note_id}: {str(e)}")
        
        logger.info("Cleanup completed!")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")

if __name__ == "__main__":
    main()
