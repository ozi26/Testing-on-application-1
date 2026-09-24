# =============================================================================
# GIT CHANGES MODULE
# This module contains functions for interacting with Git repositories.
# It uses Git commands to find out which files have changed in a commit
# or pull request.
# =============================================================================

import subprocess               # For running Git commands as subprocesses
from pathlib import Path        # For working with file paths
from analyzer.file_utils import is_config_file, is_source_file


def get_changed_files(repo_path=".", commit_range="HEAD~1..HEAD"):
    """
    Get a list of files that changed in a Git commit or range.
    
    This function runs a Git command to find out which files were
    modified, added, or deleted in a specific commit or range of commits.
    
    Args:
        repo_path: Path to the Git repository (default: current directory)
        commit_range: Git commit range to check (default: last commit)
                      Examples: "HEAD~1..HEAD", "main..feature-branch"
    
    Returns:
        A list of file paths (relative to the repository root) that changed.
        Returns an empty list if the Git command fails.
    
    Example:
        # Get files changed in the last commit
        files = get_changed_files()
        
        # Get files changed between two branches
        files = get_changed_files(commit_range="main..my-feature")
    """
    try:
        # Run the Git command to get changed files
        # --name-only: only show file names, not the actual changes
        # --diff-filter: only include Added, Copied, Modified, Renamed files
        #                (exclude Deleted files since we can't analyze them)
        result = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMR", commit_range],
            cwd=repo_path,          # Run the command in the repository directory
            capture_output=True,    # Capture stdout and stderr
            text=True,              # Return output as string (not bytes)
            check=True,             # Raise an exception if the command fails
        )
        
        # Split the output into individual file paths
        # strip() removes leading/trailing whitespace
        # split("\n") splits by newlines
        # We filter out empty strings that might appear
        changed_files = [
            line.strip()
            for line in result.stdout.strip().split("\n")
            if line.strip()
        ]
        
        # Return the list of changed files
        return changed_files
        
    except subprocess.CalledProcessError as e:
        # If the Git command fails (e.g., not a Git repository),
        # print an error message and return an empty list
        print(f"Error running git command: {e}")
        return []
    except FileNotFoundError:
        # If Git is not installed on the system,
        # print an error message and return an empty list
        print("Error: Git is not installed or not in PATH")
        return []


def categorize_changed_files(changed_files):
    """
    Separate changed files into source code files and configuration files.
    
    Args:
        changed_files: A list of file paths that have changed
    
    Returns:
        A tuple of two lists: (source_files, config_files)
        - source_files: Files with source code extensions
        - config_files: Files with configuration file extensions
    
    Example:
        files = ["main.py", "config.yaml", "utils.py"]
        source, config = categorize_changed_files(files)
        # source is ["main.py", "utils.py"]
        # config is ["config.yaml"]
    """
    # Create empty lists for each category
    source_files = []
    config_files = []
    
    # Loop through each changed file
    for file_path in changed_files:
        # Check if it's a source code file
        if is_source_file(file_path):
            source_files.append(file_path)
        # Check if it's a configuration file
        elif is_config_file(file_path):
            config_files.append(file_path)
        # Files that are neither (e.g., README.md) are ignored
    
    # Return both lists as a tuple
    return source_files, config_files