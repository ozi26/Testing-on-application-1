# =============================================================================
# FILE UTILITIES MODULE
# This module contains helper functions for reading files and extracting
# words from text. These functions are used by both the code parser and
# the configuration parser.
# =============================================================================

import re                           # 're' is Python's regular expression library
from pathlib import Path            # 'Path' helps us work with file paths easily


def read_text_file(file_path):
    """
    Read a text file and return its contents as a string.
    
    Args:
        file_path: The path to the file we want to read (can be string or Path)
    
    Returns:
        A string containing the entire file contents.
        If the file cannot be read, returns an empty string.
    
    Example:
        content = read_text_file("config.yaml")
        # content now contains the text inside config.yaml
    """
    try:
        # Path(file_path) converts the input to a Path object
        # .read_text() reads the file and returns its contents as a string
        # encoding="utf-8" ensures we can read special characters
        return Path(file_path).read_text(encoding="utf-8")
    except (FileNotFoundError, PermissionError, UnicodeDecodeError):
        # If the file doesn't exist, we don't have permission, or it's not
        # readable as text, we return an empty string instead of crashing
        return ""


def extract_words(text):
    """
    Extract all meaningful words from a piece of text.
    
    This function uses a regular expression to find words that:
    - Start with a letter (a-z, A-Z) or underscore (_)
    - Continue with letters, numbers, underscores, or dots
    
    Args:
        text: A string containing code or configuration text
    
    Returns:
        A set of lowercase words found in the text.
        Using a set means duplicates are automatically removed.
    
    Example:
        words = extract_words("payment.timeout = 30")
        # words now contains: {"payment.timeout", "30"}
    """
    # The regular expression pattern explained:
    # [A-Za-z_]     - Start with a letter or underscore
    # [A-Za-z0-9_.]* - Followed by zero or more letters, numbers, underscores, or dots
    # This captures things like "payment.timeout", "retry_attempts", "MAX_RETRIES"
    pattern = r"[A-Za-z_][A-Za-z0-9_.]*"
    
    # re.findall() finds all non-overlapping matches of the pattern
    # It returns a list of all matches found in the text
    words = re.findall(pattern, text)
    
    # We convert all words to lowercase so that "Payment" and "payment"
    # are treated as the same word. This makes matching more forgiving.
    # We return a set to remove duplicates.
    return set(word.lower() for word in words)


def get_file_extension(file_path):
    """
    Get the file extension from a file path.
    
    Args:
        file_path: The path to the file (can be string or Path)
    
    Returns:
        The file extension without the dot, in lowercase.
        Returns an empty string if there's no extension.
    
    Example:
        ext = get_file_extension("config.yaml")
        # ext is now "yaml"
    """
    # Path(file_path).suffix returns the extension including the dot
    # Example: ".yaml" or ".py"
    # We remove the dot with [1:] and convert to lowercase
    return Path(file_path).suffix.lower().lstrip(".")


def is_config_file(file_path):
    """
    Check if a file is a configuration file based on its extension.
    
    Args:
        file_path: The path to the file
    
    Returns:
        True if the file has a configuration file extension, False otherwise.
    
    Example:
        is_config_file("config.yaml")     # Returns True
        is_config_file("order_service.py") # Returns False
    """
    # Import the CONFIG_EXTENSIONS set from our config module
    from analyzer.config import CONFIG_EXTENSIONS
    
    # Get the file extension and check if it's in our set of config extensions
    return get_file_extension(file_path) in CONFIG_EXTENSIONS


def is_source_file(file_path):
    """
    Check if a file is a source code file based on its extension.
    
    Args:
        file_path: The path to the file
    
    Returns:
        True if the file has a source code extension, False otherwise.
    
    Example:
        is_source_file("order_service.py")  # Returns True
        is_source_file("config.yaml")       # Returns False
    """
    # Import the SOURCE_EXTENSIONS set from our config module
    from analyzer.config import SOURCE_EXTENSIONS
    
    # Get the file extension and check if it's in our set of source extensions
    return get_file_extension(file_path) in SOURCE_EXTENSIONS


def is_test_file(file_path):
    """
    Check if a file is a test file based on common naming patterns.
    
    Args:
        file_path: The path to the file
    
    Returns:
        True if the file appears to be a test file, False otherwise.
    
    Example:
        is_test_file("test_order.py")        # Returns True
        is_test_file("order_service_test.py") # Returns True
        is_test_file("order_service.py")      # Returns False
    """
    # Import the TEST_FILE_PATTERNS set from our config module
    from analyzer.config import TEST_FILE_PATTERNS
    
    # Get just the filename without the directory path
    filename = Path(file_path).name
    
    # Check if any of our test patterns appear in the filename
    return any(pattern in filename for pattern in TEST_FILE_PATTERNS)