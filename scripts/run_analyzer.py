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
    extract_changed_config_keys,      # ← NEW
    services_in_changed_keys,  
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
    
    # -------------------------------------------------------------------------
    # Step 4.5a: Extract affected service names
    # -------------------------------------------------------------------------
    def extract_service_name(file_path):
        """
        Extract the service name from a source code file path.
        Example: src/paymentservice/index.js -> "paymentservice"
        """
        from pathlib import Path
        parts = Path(file_path).parts
        for part in parts:
            if part.endswith("service"):
                return part
        return Path(file_path).parent.name


    def extract_services_from_config(config_file):
        """
        Extract service names from a config file's CONTENTS.
        Looks for `metadata.name` fields and hostnames like `paymentservice:50051`
        inside Kubernetes manifests. Falls back to empty set on parse errors.
        """
        from pathlib import Path
        import yaml
        import re

        services = set()
        suffix = Path(config_file).suffix.lower()

        # Only parse YAML files deeply
        if suffix not in (".yaml", ".yml"):
            return services

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                documents = list(yaml.safe_load_all(f))
        except Exception:
            return services

        for doc in documents:
            if not isinstance(doc, dict):
                continue

            # 1. metadata.name (e.g., "shippingservice")
            metadata = doc.get("metadata", {})
            if isinstance(metadata, dict):
                name = metadata.get("name")
                if isinstance(name, str) and name:
                    services.add(name)

            # 2. Hostnames inside env[].value (e.g., "paymentservice:50051")
            spec = doc.get("spec", {})
            if isinstance(spec, dict):
                template = spec.get("template", {})
                if isinstance(template, dict):
                    spec2 = template.get("spec", {})
                    if isinstance(spec2, dict):
                        containers = spec2.get("containers", []) or []
                        for container in containers:
                            if not isinstance(container, dict):
                                continue
                            env_list = container.get("env", []) or []
                            for env_var in env_list:
                                if not isinstance(env_var, dict):
                                    continue
                                value = env_var.get("value")
                                if not isinstance(value, str):
                                    continue
                                match = re.match(
                                    r"^([a-z][a-z0-9\-]*service)(:\d+)?$", value
                                )
                                if match:
                                    services.add(match.group(1))

        return services


    # Build affected services from BOTH source and config files
    affected_services = set()

    # From source code file paths
    for f in source_files:
        service = extract_service_name(f)
        if service:
            affected_services.add(service)

    # From config file CONTENTS
    # From config file CONTENTS — targeted detection
    # Instead of treating the whole config as affected, we diff the old
    # version against the new one and find which service blocks changed.
    import subprocess
    import tempfile

    for f in config_files:
        # 1. Get the OLD version of the file from Git (HEAD~1)
        #    The path stored in `f` includes the microservices-demo/ prefix,
        #    so we strip it to match Git's internal paths.
        git_path = f.replace("\\", "/")
       
        
        try:
            old_content = subprocess.run(
                ["git", "show", f"HEAD~1:{git_path}"],
                cwd="microservices-demo",
                capture_output=True,
                text=True,
                check=True,
            ).stdout
        except subprocess.CalledProcessError:
            # File didn't exist in the previous commit — treat as fully new
            old_content = ""
        
        # 2. Write the old content to a temporary file so we can parse it
        #    with the same parser as the current file.
        suffix = "." + f.rsplit(".", 1)[-1]   # e.g., ".yaml"
        with tempfile.NamedTemporaryFile(
            "w", suffix=suffix, delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(old_content)
            tmp_path = tmp.name
        
        # 3. Parse old and new versions
        old_config = parse_config_file(tmp_path)
        new_config = parse_config_file(f)

            # DEBUG: Show what we parsed
        #print(f"  [DEBUG] old_config keys: {len(old_config)}")
        #print(f"  [DEBUG] new_config keys: {len(new_config)}")
        #print(f"  [DEBUG] git_path used: {git_path}")
        #print(f"  [DEBUG] old_content length: {len(old_content)} chars")
        
        # 4. Find the keys whose values changed
        changes = extract_changed_config_keys(old_config, new_config)
        
        # 5. Extract service names from the changed keys
        config_services = services_in_changed_keys(changes.keys())
        affected_services.update(config_services)
        
        # Log what we found for transparency
        if config_services:
            print(f"  {f}: {len(changes)} key(s) changed across services "
                f"{sorted(config_services)}")
        else:
            print(f"  {f}: {len(changes)} key(s) changed, no service prefix found")

    # Fallback: if a config change had no recognizable service prefix,
    # keep the original "all services" behavior so we don't miss anything.
    for f in config_files:
        if not affected_services:
            config_services = extract_services_from_config(f)
            affected_services.update(config_services)

    print(f"Affected services: {sorted(affected_services)}")

    # -------------------------------------------------------------------------
    # Step 4.5b: Compute service-relevance scores for each test file
    # (this must come AFTER affected_services has been built)
    # -------------------------------------------------------------------------
    from analyzer.scoring import compute_service_relevance

    service_relevance = {
        test_file: compute_service_relevance(test_file, affected_services)
        for test_file in test_files
    }
    print(f"Service-relevance scores computed for {len(service_relevance)} test(s)")

    # Step 5: Rank tests by combined score
    print("\n[Step 5] Ranking tests by relevance...")
    from analyzer.scoring import calculate_score

    # Weighting: service relevance is the dominant signal.
    # Lexical overlap is a weaker tie-breaker.
    WEIGHT_LEXICAL = 0.4
    WEIGHT_SERVICE = 0.6

    scored_tests = []
    for test_file in test_files:
        # Base lexical score (0.0 to 1.0)
        lexical_score = calculate_score(all_terms, test_file)
        
        # Service relevance (0.0 to 1.0)
        service_score = service_relevance.get(test_file, 0.0)
        
        # Weighted combination
        final_score = (
            WEIGHT_LEXICAL * lexical_score
            + WEIGHT_SERVICE * service_score
        )
        
        if final_score > 0:
            scored_tests.append((test_file, final_score))

    # Sort descending
    scored_tests.sort(key=lambda x: x[1], reverse=True)

    # Apply threshold — only include tests with real signal
    threshold = 0.30
    ranked_tests = [(t, s) for t, s in scored_tests if s >= threshold]

    print(f"Ranked tests ({len(ranked_tests)} above threshold {threshold}):")
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
        # Write at the current working directory (the workspace root),
        # NOT inside the target repo. This keeps Jenkins simple.
        output_path = Path("analyzer_result.json")
        
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