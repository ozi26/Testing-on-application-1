# =============================================================================
# LANGUAGE DETECTION MODULE
# Detects the primary language(s) of a project by looking at well-known files.
# This is informational only — the analyzer works regardless.
# =============================================================================

from pathlib import Path


# Maps marker files to their language names
LANGUAGE_MARKERS = {
    "package.json":       "JavaScript / Node.js",
    "tsconfig.json":      "TypeScript",
    "pom.xml":            "Java (Maven)",
    "build.gradle":       "Java (Gradle)",
    "build.gradle.kts":   "Kotlin (Gradle)",
    "go.mod":             "Go",
    "Cargo.toml":         "Rust",
    "Gemfile":            "Ruby",
    "composer.json":      "PHP",
    "requirements.txt":   "Python (pip)",
    "pyproject.toml":     "Python (modern)",
    "setup.py":           "Python (legacy)",
    "Pipfile":            "Python (pipenv)",
    "pubspec.yaml":       "Dart / Flutter",
    "mix.exs":            "Elixir",
    "*.csproj":           "C# (.NET)",
    "*.sln":              "C# / .NET Solution",
}


def detect_languages(project_root):
    """
    Detect languages used in a project based on marker files.
    
    Args:
        project_root: Path to the project root
    
    Returns:
        A list of detected language names.
    """
    root = Path(project_root)
    detected = []
    
    for marker, language in LANGUAGE_MARKERS.items():
        # Handle glob patterns (e.g., "*.csproj")
        if "*" in marker:
            if any(root.glob(marker)):
                detected.append(language)
        else:
            if (root / marker).exists():
                detected.append(language)
    
    return detected


def print_detected_languages(project_root="."):
    """Print detected languages for informational purposes."""
    languages = detect_languages(project_root)
    if languages:
        print(f"Detected languages: {', '.join(languages)}")
    else:
        print("No known language markers found.")
    return languages