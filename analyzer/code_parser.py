# =============================================================================
# CODE PARSER MODULE
# This module contains functions for parsing source code files and
# extracting meaningful words from them. This is the core of the
# lexical analysis approach - we treat code like text.
# =============================================================================

from pathlib import Path            # For working with file paths
from analyzer.file_utils import extract_words, read_text_file


def parse_source_file(file_path):
    """
    Parse a source code file and extract words from it.
    
    This function reads a source code file and extracts all meaningful
    words from it. These words are then used to match against test files
    to determine which tests are relevant.
    
    Args:
        file_path: The path to the source code file
    
    Returns:
        A set of lowercase words found in the file.
        Returns an empty set if the file cannot be read.
    
    Example:
        # If PaymentService.java contains:
        # public class PaymentService {
        #     public void processPayment() { ... }
        # }
        #
        # parse_source_file("PaymentService.java") returns:
        # {"public", "class", "paymentservice", "void", "processpayment", ...}
    """
    # Read the entire file as text
    content = read_text_file(file_path)
    
    # If the file couldn't be read, return an empty set
    if not content:
        return set()
    
    # Extract words from the content using our lexical analysis function
    return extract_words(content)


def extract_code_terms(changed_files):
    """
    Extract searchable terms from a list of changed source code files.
    
    This function takes a list of file paths that have changed and
    extracts all the words from them. These words are then used to
    find relevant tests.
    
    Args:
        changed_files: A list of file paths that have changed
    
    Returns:
        A set of lowercase words found in all the changed files combined.
    
    Example:
        files = ["PaymentService.java", "OrderService.java"]
        terms = extract_code_terms(files)
        # terms contains all words from both files
    """
    # Create an empty set to store all the terms
    terms = set()
    
    # Loop through each changed file
    for file_path in changed_files:
        # Parse the file and extract words
        file_terms = parse_source_file(file_path)
        
        # Add the words to our combined set
        terms.update(file_terms)
    
    # Return the combined set of terms
    return terms