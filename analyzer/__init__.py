# This file makes the 'analyzer' folder a Python package.
# When Python sees this file, it knows this folder contains importable modules.

# We define what should be exported when someone does 'from analyzer import *'
__all__ = [
    'config',           # File extension definitions
    'file_utils',       # File reading and word extraction
    'config_parser',    # Configuration file parsing
    'code_parser',      # Source code parsing
    'git_changes',      # Git changeset detection
    'scoring',          # Test relevance scoring
    'selector',         # Affected test selection
    'telemetry',        # OpenTelemetry setup
    'tracing',          # Runtime config access tracking
]