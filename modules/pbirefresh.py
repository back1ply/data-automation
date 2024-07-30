import os
import logging

# Get the logger
logger = logging.getLogger("functions")

def create_blank_text_file(directory, filename):

    # Ensure the directory exists
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    # Define the full file path
    file_path = os.path.join(directory, filename)

    # Create a blank text file
    with open(file_path, 'w') as file:
        pass  # 'pass' does nothing, just creates an empty file

    logger.info(f"Blank text file created at: {file_path}")
