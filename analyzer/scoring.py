# =============================================================================
# SCORING MODULE
# This module contains functions for calculating how relevant a test is
# to a set of changes. It uses lexical matching - comparing words in
# changed files with words in test files.
# =============================================================================

from analyzer.file_utils import extract_words, read_text_file


def calculate_score(changed_terms, test_file_path):
    """
    Calculate a relevance score between changed terms and a test file.
    
    This function compares the words extracted from changed files with
    the words in a test file. The more words they have in common, the
    higher the score, meaning the test is more likely to be affected.
    
    Args:
        changed_terms: A set of words from the changed files
        test_file_path: Path to the test file to score
    
    Returns:
        A float between 0.0 and 1.0 representing the relevance score.
        Higher scores mean the test is more likely to be affected.
    
    Example:
        changed_terms = {"payment", "timeout", "retry"}
        score = calculate_score(changed_terms, "test_payment.py")
        # If test_payment.py contains "payment" and "timeout",
        # the score will be higher than if it doesn't contain them.
    """
    # Read the test file content
    test_content = read_text_file(test_file_path)
    
    # If the test file couldn't be read, return a score of 0
    if not test_content:
        return 0.0
    
    # Extract words from the test file
    test_terms = extract_words(test_content)
    
    # If the test file has no words, return a score of 0
    if not test_terms:
        return 0.0
    
    # Find the intersection (common words) between changed terms and test terms
    common_terms = changed_terms.intersection(test_terms)
    
    # Calculate the score as the ratio of common terms to changed terms
    # This gives us a value between 0 and 1
    # A score of 1.0 means the test contains ALL the changed terms
    # A score of 0.0 means the test contains NONE of the changed terms
    base_score = len(common_terms) / len(changed_terms) if changed_terms else 0.0

    # Add filename-based bonus
    bonus = filename_match_bonus(test_file_path, test_file_path)

    # Return the calculated score
    return min(base_score + bonus, 1.0)

def compute_service_relevance(test_file, affected_services):
    """
    Compute a service-relevance score between 0.0 and 1.0 based on
    how strongly a test file is tied to an affected service.
    
    Scoring:
      - 1.0: Test filename directly names the affected service
             (e.g., paymentservice.test.js when paymentservice changed)
      - 0.7: Test filename contains the service root word
             (e.g., payment_flow.test.js when paymentservice changed)
      - 0.4: Test file content explicitly mentions the affected service
      - 0.2: Test file content mentions the service root word
      - 0.0: No match at all
    
    Args:
        test_file: Path to the test file
        affected_services: Set of service names that changed
    
    Returns:
        A float between 0.0 and 1.0.
    """
    from pathlib import Path
    from analyzer.file_utils import read_text_file
    
    best_score = 0.0
    filename = Path(test_file).stem.lower()
    
    try:
        content = read_text_file(test_file).lower()
    except Exception:
        content = ""
    
    for service in affected_services:
        service_lower = service.lower()          # e.g. "paymentservice"
        root = service_lower.replace("service", "").strip()  # e.g. "payment"
        
        # --- Filename matches (strongest signals) ---
        if service_lower and service_lower in filename:
            best_score = max(best_score, 1.0)
            continue
        
        # Root-word match in filename (e.g. "payment" in "payment_test")
        if len(root) >= 4 and root in filename:
            best_score = max(best_score, 0.7)
            continue
        
        # --- Content matches (weaker signals) ---
        # Count occurrences to distinguish a strong mention from a passing reference
        if service_lower and service_lower in content:
            best_score = max(best_score, 0.4)
            continue
        
        if len(root) >= 5 and root in content:
            # Count occurrences: more mentions = stronger signal
            occurrences = content.count(root)
            score = min(0.2 + (0.05 * occurrences), 0.4)
            best_score = max(best_score, score)
    
    return best_score

def filename_match_bonus(changed_file, test_file):
    """
    Return a bonus score if the test filename shares service names
    with the changed file.
    """
    from pathlib import Path
    
    changed_name = Path(changed_file).stem.lower()
    test_name = Path(test_file).stem.lower()
    
    # Extract the service name (remove common suffixes)
    for suffix in ["_service", "service", "_test", "test", "_spec", "spec"]:
        changed_name = changed_name.replace(suffix, "")
        test_name = test_name.replace(suffix, "")
    
    # If they share the service name, give a boost
    if changed_name and changed_name in test_name:
        return 0.3
    
    return 0.0

def rank_tests(changed_terms, test_files, threshold=0.1):
    """
    Rank test files by their relevance to the changed terms.
    
    This function calculates a score for each test file and returns
    them sorted from most relevant to least relevant.
    
    Args:
        changed_terms: A set of words from the changed files
        test_files: A list of paths to test files
        threshold: Minimum score to include a test (default: 0.1)
                   Tests with scores below this threshold are excluded.
    
    Returns:
        A list of tuples (test_file, score) sorted by score (highest first).
        Only includes tests with scores above the threshold.
    
    Example:
        terms = {"payment", "timeout"}
        tests = ["test_payment.py", "test_order.py", "test_inventory.py"]
        ranked = rank_tests(terms, tests)
        # ranked might be:
        # [("test_payment.py", 0.8), ("test_order.py", 0.2)]
        # (test_inventory.py is excluded if its score is below 0.1)
    """
    # Create a list to store (test_file, score) tuples
    scores = []
    
    # Loop through each test file
    for test_file in test_files:
        # Calculate the relevance score for this test
        score = calculate_score(changed_terms, test_file)
        
        # Only include tests with scores above the threshold
        if score >= threshold:
            scores.append((test_file, score))
    
    # Sort the list by score in descending order (highest score first)
    # key=lambda x: x[1] means sort by the second element of each tuple (the score)
    # reverse=True means descending order
    scores.sort(key=lambda x: x[1], reverse=True)
    
    # Return the sorted list
    return scores