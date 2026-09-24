# =============================================================================
# RUN ANALYZER
# This is the main entry point for the Test Impact Analyzer.
# It ties together all the components:
# - Git changeset detection
# - Source code and configuration parsing
# - Test scoring and selection
# =============================================================================

import sys                      # For modifying Python path
from pathlib import Path        # For working with file paths

# Add the project root to Python's path so we can import our modules
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# ============= Import our analyzer modules =====================

from analyzer.git_changes import get_changed_files, categorize_changed_files
from analyzer.code_parser import extract_code_terms
from analyzer.config_parser import (
    parse_config_file,      # Parse a config file into a flat dictionary
    find_config_changes,    # Find what changed between two configs
    extract_config_terms,   # Extract searchable terms from changes
)
from analyzer.scoring import rank_tests
from analyzer.file_utils import read_text_file


def find_test_files(test_dir):
    """
    Find all test files in a directory, across any programming language.
    
    Uses the TEST_FILE_PATTERNS from analyzer.config to detect tests
    by filename convention, regardless of extension.
    
    Args:
        test_dir: The directory to search for test files
    
    Returns:
        A list of paths to test files.
    """
    from analyzer.config import SOURCE_EXTENSIONS, TEST_FILE_PATTERNS
    from analyzer.file_utils import get_file_extension
    
    test_path = Path(test_dir)
    
    if not test_path.exists():
        return []
    
    test_files = []
    
    # Walk through every file in the test directory
    for file_path in test_path.rglob("*"):
        # Skip directories
        if not file_path.is_file():
            continue
        
        # Skip files with extensions that aren't source-code-like
        extension = get_file_extension(file_path)
        if extension not in SOURCE_EXTENSIONS:
            continue
        
        # Check if the filename matches any test pattern
        filename = file_path.name
        if any(pattern in filename for pattern in TEST_FILE_PATTERNS):
            test_files.append(str(file_path))
    
    return test_files


def analyze_changes(repo_path=".", commit_range="HEAD~1..HEAD", test_dir="tests"):
    """
    Analyze changes and select affected tests.
    
    This is the main function that ties everything together.
    
    Args:
        repo_path: Path to the Git repository
        commit_range: Git commit range to analyze
        test_dir: Directory containing test files
    
    Returns:
        A dictionary with the analysis results.
    """
    print("=" * 60)
    print("TEST IMPACT ANALYZER")
    print("=" * 60)
    
    # Step 1: Get changed files from Git
    print("\n[Step 1] Getting changed files from Git...")
    changed_files = get_changed_files(repo_path, commit_range)
    
    if not changed_files:
        print("No changed files found. Nothing to analyze.")
        return {"error": "No changes found"}
    
    print(f"Found {len(changed_files)} changed file(s):")
    for f in changed_files:
        print(f"  - {f}")
    
    # Step 2: Categorize files into source and config
    print("\n[Step 2] Categorizing changed files...")
    source_files, config_files = categorize_changed_files(changed_files)
    
    print(f"Source code files ({len(source_files)}):")
    for f in source_files:
        print(f"  - {f}")
    
    print(f"Configuration files ({len(config_files)}):")
    for f in config_files:
        print(f"  - {f}")
    
    # Step 3: Extract terms from changed files
    print("\n[Step 3] Extracting terms from changed files...")
    
    # Extract terms from source code files
    code_terms = extract_code_terms(source_files)
    print(f"Extracted {len(code_terms)} terms from source code files")
    
    # Extract terms from configuration files
    config_terms = set()
    for config_file in config_files:
        # For config files, we need to compare old and new versions
        # For simplicity, we'll just extract terms from the current version
        # In a real implementation, you'd use Git to get the old version
        config_data = parse_config_file(config_file)
        for key in config_data.keys():
            # Extract words from the key
            from analyzer.file_utils import extract_words
            config_terms.update(extract_words(key))
    
    print(f"Extracted {len(config_terms)} terms from configuration files")
    
    # Combine all terms
    all_terms = code_terms | config_terms
    print(f"Total unique terms: {len(all_terms)}")
    
    # Step 4: Find test files
    print("\n[Step 4] Finding test files...")
    test_files = find_test_files(test_dir)
    print(f"Found {len(test_files)} test file(s):")
    for f in test_files:
        print(f"  - {f}")
    
    if not test_files:
        print("No test files found. Nothing to score.")
        return {"error": "No test files found"}
    
    # Step 5: Rank tests by relevance
    print("\n[Step 5] Ranking tests by relevance...")
    ranked_tests = rank_tests(all_terms, test_files, threshold=0.05)
    
    print(f"\nRanked tests ({len(ranked_tests)} above threshold):")
    for test_file, score in ranked_tests:
        print(f"  {score:.3f}  {test_file}")
    
    # Step 6: Return results
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    
    return {
        "changed_files": changed_files,
        "source_files": source_files,
        "config_files": config_files,
        "code_terms": code_terms,
        "config_terms": config_terms,
        "all_terms": all_terms,
        "test_files": test_files,
        "ranked_tests": ranked_tests,
    }


def main():
    """
    Main function that runs the analyzer with command-line arguments.
    """
    import argparse
    
    # Create an argument parser
    parser = argparse.ArgumentParser(
        description="Test Impact Analyzer - Select affected tests based on changes"
    )
    
    # Add arguments
    parser.add_argument(
        "--repo",
        default=".",
        help="Path to the Git repository (default: current directory)",
    )
    parser.add_argument(
        "--range",
        default="HEAD~1..HEAD",
        help="Git commit range to analyze (default: HEAD~1..HEAD)",
    )
    parser.add_argument(
        "--tests",
        default="tests",
        help="Directory containing test files (default: tests)",
    )
    
    # Parse the arguments
    args = parser.parse_args()
    
    # Run the analysis
    results = analyze_changes(
        repo_path=args.repo,
        commit_range=args.range,
        test_dir=args.tests,
    )

    # ===== JENKINS INTEGRATION: Write JSON output =====
    import json
    from pathlib import Path
    
    # Only write output if analysis succeeded (no errors)
    if "error" not in results:
        output_path = Path(args.repo) / "analyzer_result.json"
        
        # Build the data Jenkins needs
        jenkins_output = {
            "affected_tests": [test for test, score in results["ranked_tests"]],
            "has_affected_tests": len(results["ranked_tests"]) > 0,
            "test_count": len(results["ranked_tests"]),
        }
        
        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(jenkins_output, f, indent=2)
        
        print(f"[Jenkins] Result written to: {output_path}")
        print(f"[Jenkins] Affected tests: {jenkins_output['test_count']}")
    # ===== END JENKINS INTEGRATION =====
    
    # Return a success or failure code
    if "error" in results:
        sys.exit(1)
    else:
        sys.exit(0)


# This block runs when the script is executed directly
if __name__ == "__main__":
    main()