"""
File Utility Functions

Helpers for file operations, path handling, and related tasks.
"""

import os
import logging
import json
import csv
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


def ensure_directory_exists(directory_path):
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        directory_path (str): Path to the directory

    Returns:
        bool: True if directory exists or was created successfully
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {directory_path}: {str(e)}")
        return False


def safe_file_write(file_path, content, mode='w', encoding='utf-8'):
    """
    Safely write content to a file with error handling.

    Args:
        file_path (str): Path to write the file
        content (str): Content to write
        mode (str): File open mode ('w', 'wb', 'a', etc.)
        encoding (str): File encoding (for text modes)

    Returns:
        bool: True if write succeeded, False if it failed
    """
    try:
        # Ensure the directory exists
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        # Write the file
        with open(file_path, mode=mode, encoding=encoding if 'b' not in mode else None) as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"Error writing to file {file_path}: {str(e)}")
        return False


def safe_file_read(file_path, mode='r', encoding='utf-8', default=None):
    """
    Safely read content from a file with error handling.

    Args:
        file_path (str): Path to the file to read
        mode (str): File open mode ('r', 'rb', etc.)
        encoding (str): File encoding (for text modes)
        default: Value to return if file cannot be read

    Returns:
        Content of the file or default value if error
    """
    try:
        with open(file_path, mode=mode, encoding=encoding if 'b' not in mode else None) as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return default


def get_file_extension(file_path):
    """
    Get the extension of a file.

    Args:
        file_path (str): Path to the file

    Returns:
        str: Extension without the dot, lowercase
    """
    return os.path.splitext(file_path)[1].lower().lstrip('.')


def list_files_by_extension(directory, extension=None, recursive=False):
    """
    List all files in a directory with an optional extension filter.

    Args:
        directory (str): Directory to search
        extension (str, optional): File extension to filter by (without dot)
        recursive (bool): Whether to search recursively

    Returns:
        list: List of file paths matching the criteria
    """
    if not os.path.exists(directory):
        return []

    result = []

    if recursive:
        # Walk through all subdirectories
        for root, dirs, files in os.walk(directory):
            for file in files:
                if extension is None or file.lower().endswith(f".{extension.lower()}"):
                    result.append(os.path.join(root, file))
    else:
        # Just list files in the top directory
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path) and (extension is None or
                                              file.lower().endswith(f".{extension.lower()}")):
                result.append(file_path)

    return result


def safe_json_read(file_path, default=None):
    """
    Safely read and parse a JSON file.

    Args:
        file_path (str): Path to the JSON file
        default: Value to return if file cannot be read or parsed

    Returns:
        dict/list: Parsed JSON data or default value if error
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading JSON file {file_path}: {str(e)}")
        return default if default is not None else {}


def safe_json_write(file_path, data, indent=2):
    """
    Safely write data to a JSON file.

    Args:
        file_path (str): Path to write the JSON file
        data (dict/list): Data to serialize to JSON
        indent (int): Indentation level for pretty printing

    Returns:
        bool: True if write succeeded, False if it failed
    """
    try:
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent)
        return True
    except Exception as e:
        logger.error(f"Error writing JSON to {file_path}: {str(e)}")
        return False


def safe_csv_read(file_path, delimiter=',', quotechar='"', default=None):
    """
    Safely read and parse a CSV file.

    Args:
        file_path (str): Path to the CSV file
        delimiter (str): CSV delimiter character
        quotechar (str): CSV quote character
        default: Value to return if file cannot be read or parsed

    Returns:
        list: List of rows as dictionaries or default value if error
    """
    try:
        with open(file_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f, delimiter=delimiter, quotechar=quotechar)
            return list(reader)
    except Exception as e:
        logger.error(f"Error reading CSV file {file_path}: {str(e)}")
        return default if default is not None else []


def safe_csv_write(file_path, data, fieldnames=None, delimiter=',', quotechar='"'):
    """
    Safely write data to a CSV file.

    Args:
        file_path (str): Path to write the CSV file
        data (list): List of dictionaries to write as CSV rows
        fieldnames (list): List of field names for the CSV header
        delimiter (str): CSV delimiter character
        quotechar (str): CSV quote character

    Returns:
        bool: True if write succeeded, False if it failed
    """
    try:
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        # If fieldnames not provided, try to get from first row
        if fieldnames is None and data and isinstance(data[0], dict):
            fieldnames = list(data[0].keys())

        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter,
                                    quotechar=quotechar, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            writer.writerows(data)
        return True
    except Exception as e:
        logger.error(f"Error writing CSV to {file_path}: {str(e)}")
        return False


def get_temp_file_path(prefix="temp", suffix=".tmp"):
    """
    Generate a temporary file path.

    Args:
        prefix (str): Prefix for the filename
        suffix (str): Suffix for the filename (typically the extension)

    Returns:
        str: Path to a temporary file
    """
    import tempfile
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
    os.close(fd)  # Close the file descriptor
    return path


def safe_file_copy(source, destination, overwrite=True):
    """
    Safely copy a file from source to destination.

    Args:
        source (str): Source file path
        destination (str): Destination file path
        overwrite (bool): Whether to overwrite existing destination

    Returns:
        bool: True if copy succeeded, False if it failed
    """
    try:
        if not os.path.exists(source):
            logger.error(f"Source file does not exist: {source}")
            return False

        if os.path.exists(destination) and not overwrite:
            logger.warning(f"Destination file exists and overwrite=False: {destination}")
            return False

        directory = os.path.dirname(destination)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        shutil.copy2(source, destination)
        return True
    except Exception as e:
        logger.error(f"Error copying file from {source} to {destination}: {str(e)}")
        return False