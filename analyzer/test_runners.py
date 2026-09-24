# =============================================================================
# TEST RUNNERS MODULE
# This module maps file extensions to the appropriate test runner command.
# Adding a new language here is all you need to run its tests.
# =============================================================================

import subprocess
import sys
from pathlib import Path


# -----------------------------------------------------------------------------
# TEST RUNNER REGISTRY
# Maps file extension -> (command template, extra args)
# The {files} placeholder gets replaced with the actual test file paths.
# -----------------------------------------------------------------------------
TEST_RUNNERS = {
    # Python -> pytest
    "py": {
        "command": [sys.executable, "-m", "pytest"],
        "args": ["-v"],
        "name": "pytest",
    },
    
    # JavaScript / TypeScript -> npm test
    "js":  {"command": ["npm", "test", "--"], "args": [], "name": "npm (jest/mocha)"},
    "jsx": {"command": ["npm", "test", "--"], "args": [], "name": "npm"},
    "ts":  {"command": ["npm", "test", "--"], "args": [], "name": "npm"},
    "tsx": {"command": ["npm", "test", "--"], "args": [], "name": "npm"},
    "mjs": {"command": ["npm", "test", "--"], "args": [], "name": "npm"},
    "cjs": {"command": ["npm", "test", "--"], "args": [], "name": "npm"},
    
    # Java -> mvn test
    "java": {"command": ["mvn", "test", "-Dtest="], "args": [], "name": "maven"},
    "kt":   {"command": ["mvn", "test", "-Dtest="], "args": [], "name": "maven"},
    
    # Go -> go test
    "go": {"command": ["go", "test"], "args": ["-v"], "name": "go test"},
    
    # Ruby -> rspec
    "rb": {"command": ["rspec"], "args": [], "name": "rspec"},
    
    # PHP -> phpunit
    "php": {"command": ["phpunit"], "args": [], "name": "phpunit"},
    
    # Rust -> cargo test
    "rs": {"command": ["cargo", "test"], "args": [], "name": "cargo test"},
    
    # C / C++ -> ctest (common)
    "c":   {"command": ["ctest"], "args": ["--output-on-failure"], "name": "ctest"},
    "cpp": {"command": ["ctest"], "args": ["--output-on-failure"], "name": "ctest"},
}


def get_runner_for_extension(extension):
    """
    Look up the test runner configuration for a file extension.
    
    Args:
        extension: File extension (without the dot)
    
    Returns:
        A dict with 'command', 'args', and 'name' keys,
        or None if no runner is registered for this extension.
    """
    return TEST_RUNNERS.get(extension)


def group_tests_by_runner(test_files):
    """
    Group test files by their required test runner.
    
    Args:
        test_files: A list of file paths
    
    Returns:
        A dict mapping runner name -> (runner_config, list_of_files)
    """
    from analyzer.file_utils import get_file_extension
    
    groups = {}
    for test_file in test_files:
        ext = get_file_extension(test_file)
        runner = get_runner_for_extension(ext)
        
        if runner is None:
            # Unknown extension — put in a special group
            runner_name = f"unknown ({ext})"
            runner = None
        else:
            runner_name = runner["name"]
        
        if runner_name not in groups:
            groups[runner_name] = (runner, [])
        
        groups[runner_name][1].append(test_file)
    
    return groups


def run_tests_for_group(runner, test_files):
    """
    Execute the appropriate test runner for a group of test files.
    
    Args:
        runner: The runner configuration dict (or None for unknown)
        test_files: List of test file paths
    
    Returns:
        Exit code (0 = success, non-zero = failure)
    """
    if runner is None:
        print(f"  [SKIP] No test runner configured for: {test_files}")
        return 0
    
    # Build the command
    cmd = list(runner["command"]) + test_files + list(runner["args"])
    
    print(f"\n  Running with {runner['name']}:")
    print(f"    {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd)
        return result.returncode
    except FileNotFoundError:
        print(f"  [ERROR] {runner['name']} is not installed or not in PATH")
        return 127  # Standard "command not found" exit code