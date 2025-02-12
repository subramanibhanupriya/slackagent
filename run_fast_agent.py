import asyncio
from fast_agent_processor import FastAgentProcessor
import os

async def run_demo():
    # Initialize the processor with 5 worker threads
    processor = FastAgentProcessor(max_workers=5)
    
    # Start background processing
    processor.start_processing()
    
    try:
        # Get user input for folder creation
        folder_name = input("Enter the name of the folder to create: ")
        meeting_name = input("Enter the name of the meeting: ")
        
        # Create the folder
        folder_path = os.path.join(os.getcwd(), folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"Folder '{folder_name}' created successfully.")
        else:
            print(f"Folder '{folder_name}' already exists.")
        
        # Create a test file for meeting notes
        meeting_notes_file = os.path.join(folder_path, f"{meeting_name}_notes.txt")
        
        # Write some content to the meeting notes file
        with open(meeting_notes_file, "w") as f:
            f.write("This is a sample meeting note.")
        
        # Prepare batch data for processing
        batch_data = {
            'messages': [
                {'id': 1, 'text': '🚀 Test message 1 - Fast Agent'},
                {'id': 2, 'text': '📝 Test message 2 - Processing Demo'}
            ],
            'files': [
                meeting_notes_file
            ],
            'tasks': [
                {'id': 1, 'type': 'process', 'data': 'Task 1 data'},
                {'id': 2, 'type': 'analyze', 'data': 'Task 2 data'}
            ]
        }
        
        print("\n=== Starting Fast Agent Demo ===")
        print("Processing batch with:")
        print(f"- {len(batch_data['messages'])} messages")
        print(f"- {len(batch_data['files'])} files")
        print(f"- {len(batch_data['tasks'])} tasks")
        print("==============================")
        
        # Process the batch
        results = await processor.process_batch(batch_data)
        
        # Display results
        print("\n=== Processing Results ===")
        
        # Message results
        print("\nMessage Results:")
        for msg_result in results['message_results']:
            status = "✅" if msg_result['status'] == 'success' else "❌"
            print(f"{status} Message {msg_result['message_id']}")
        
        # File results
        print("\nFile Results:")
        for file_result in results['file_results']:
            status = "✅" if file_result['status'] == 'success' else "❌"
            print(f"{status} File: {os.path.basename(file_result['file_path'])}")
        
        # Task results
        print("\nTask Results:")
        for task_result in results['task_results']:
            status = "✅" if task_result['status'] == 'completed' else "❌"
            print(f"{status} Task {task_result['task_id']} - "
                  f"Processing time: {task_result['processing_time']:.2f}s")
        
        print("\n=== Demo Completed ===")
        
    finally:
        # Clean up
        processor.stop_processing()
        
        # Remove test files
        if os.path.exists(meeting_notes_file):
            os.remove(meeting_notes_file)
        if os.path.exists(folder_path):
            os.rmdir(folder_path)

if __name__ == "__main__":
    # Run the async demo
    asyncio.run(run_demo())