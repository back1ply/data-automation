import shutil
import os
import win32com
import datetime
import logging

# Get the logger
logger = logging.getLogger("functions")

def remove_temp_folders():
    # Define the directory path
    try:
        directory_path = win32com.__gen_path__
    except AttributeError as e:
        logger.error(f"Directory path not available: {e}")
        return

    # Iterate through items in the directory
    if os.path.exists(directory_path) and os.path.isdir(directory_path):
        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)
            
            # Check if the item is a directory
            if os.path.isdir(item_path):
                # Remove the directory
                try:
                    shutil.rmtree(item_path)
                    logger.info(f"Removed folder: {item_path}")
                except OSError as e:
                    logger.error(f"Error removing folder {item_path}: {e}")
    
    else:
        logger.error(f"Directory path {directory_path} does not exist or is not a directory.")
        print("I came here")
        return
    logger.info(f"No directory to be removed in {directory_path}.")
    return

def remove_file_if_exists(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        logger.info(f"File '{file_path}' removed.")

def check_and_create_directory(file_path):
    # Get the directory and file name from the file path
    directory = os.path.dirname(file_path)
    file_name = os.path.basename(file_path)
    
    # Remove the file extension from the file name
    file_name_without_ext = os.path.splitext(file_name)[0]
    
    # Construct the full path for the new directory
    new_directory_path = os.path.join(directory, file_name_without_ext)
    logger.info(f"Creating Directory '{new_directory_path}'....")
    # Check if the directory already exists
    if os.path.isdir(new_directory_path):
        # Directory exists, log the event and exit the function
        logger.info(f"Directory '{new_directory_path}' already exists.")
    else:
        # Directory does not exist, create it
        os.makedirs(new_directory_path)
        logger.info(f"Directory '{new_directory_path}' created successfully.")
    return new_directory_path
    
def clear_gen_path():
    # Define the directory path
    directory_path = win32com.__gen_path__

    # Iterate through items in the directory
    for item in os.listdir(directory_path):
        item_path = os.path.join(directory_path, item)
        
        # Check if the item is a directory
        if os.path.isdir(item_path):
            # Remove the directory
            try:
                shutil.rmtree(item_path)
                print(f"Removed folder: {item_path}")
            except OSError as e:
                print(f"Error removing folder {item_path}: {e}")

def get_current_time_string():
    # Get the current date and time
    now = datetime.now()
    
    # Format the date and time as YYYYMMDDHHMM
    time_string = now.strftime("%Y%m%d%H%M%S")

    return time_string