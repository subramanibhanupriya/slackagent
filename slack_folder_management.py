import os

# Function to iterate through files in a specified folder
def process_folder(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            # Logic to process each file for querying
            pass
