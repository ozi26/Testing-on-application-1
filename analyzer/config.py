# =============================================================================
# CONFIGURATION MODULE
# This module stores all the file extension definitions used throughout
# the analyzer. By keeping them in one place, it's easy to add support
# for new file types later.
# =============================================================================

# -----------------------------------------------------------------------------
# CONFIGURATION FILE EXTENSIONS
# These are the file extensions we treat as "configuration files".
# When a file with one of these extensions changes, we know we need to
# parse it differently from source code files.
# -----------------------------------------------------------------------------
CONFIG_EXTENSIONS = {
    "yml",          # YAML files (used by Kubernetes, Docker Compose, etc.)
    "yaml",         # YAML files (alternative extension)
    "properties",   # Java properties files
    "json",         # JSON configuration files
    "xml",          # XML configuration files
}

# -----------------------------------------------------------------------------
# SOURCE CODE FILE EXTENSIONS
# These are the file extensions we treat as "source code files".
# When a file with one of these extensions changes, we extract words
# from it and compare with words in test files.
# -----------------------------------------------------------------------------
SOURCE_EXTENSIONS = {
    # Python
    "py",
    # Java / JVM
    "java", "kt", "scala", "groovy",
    # JavaScript / TypeScript
    "js", "jsx", "ts", "tsx", "mjs", "cjs",
    # C family
    "c", "cpp", "cc", "cxx", "h", "hpp", "cs",
    # Go
    "go",
    # Ruby
    "rb",
    # PHP
    "php",
    # Rust
    "rs",
    # Swift / Objective-C
    "swift", "m", "mm",
    # Shell
    "sh", "bash", "zsh",
    # Kotlin / Dart / Elixir / Erlang
    "dart", "ex", "exs", "erl", "hrl",
    # Lua / Perl / R
    "lua", "pl", "pm", "r",
}

# -----------------------------------------------------------------------------
# TEST FILE PATTERNS
# These patterns help us identify which files are test files.
# A file is considered a test file if its name contains any of these patterns.
# -----------------------------------------------------------------------------
TEST_FILE_PATTERNS = {
    # Python: test_order.py, order_test.py
    "test_", "_test",
    
    # Java / C# / Kotlin: OrderTest.java, OrderTests.kt
    "Test", "Tests", "IT",  # IT = Integration Test
    
    # JavaScript / TypeScript: order.test.js, order.spec.ts
    ".test.", ".spec.", "_spec.",
    
    # Ruby: order_spec.rb
    "_spec",
    
    # Go: order_test.go
    "_test",
    
    # Generic
    "spec",
}