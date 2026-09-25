# =============================================================================
# CONFIGURATION PARSER MODULE
# This module contains functions for parsing different types of configuration
# files and extracting their key-value pairs. When a configuration file
# changes, we use these functions to understand what settings were modified.
# =============================================================================

import json                         # For parsing JSON files
import xml.etree.ElementTree as ET  # For parsing XML files
import yaml                         # For parsing YAML files (PyYAML library)
from pathlib import Path            # For working with file paths


def flatten_dictionary(data, parent_key=""):
    """
    Flatten a nested dictionary into a single-level dictionary.
    
    Configuration files often have nested structures like:
    {
        "server": {
            "timeout": 30,
            "retry": {
                "attempts": 3
            }
        }
    }
    
    This function converts that to:
    {
        "server.timeout": 30,
        "server.retry.attempts": 3
    }
    
    This makes it easier to compare old and new configurations.
    
    Args:
        data: The dictionary to flatten (can be nested)
        parent_key: The prefix to add to all keys (used in recursion)
    
    Returns:
        A flat dictionary with dot-separated keys.
    
    Example:
        nested = {"server": {"timeout": 30}}
        flat = flatten_dictionary(nested)
        # flat is now {"server.timeout": 30}
    """
    # Create an empty dictionary to store our flattened results
    result = {}
    
    # If the input is not a dictionary, return an empty dictionary
    # This handles cases where we have a list or a simple value
    if not isinstance(data, dict):
        return result
    
    # Loop through each key-value pair in the dictionary
    for key, value in data.items():
        # Build the full key by joining parent_key and current key with a dot
        # If parent_key is empty (first level), just use the key
        if parent_key:
            full_key = f"{parent_key}.{key}"
        else:
            full_key = str(key)
        
        # If the value is another dictionary, recursively flatten it
        if isinstance(value, dict):
            # Recursively call flatten_dictionary and merge results
            result.update(flatten_dictionary(value, full_key))
        else:
            # If the value is not a dictionary, add it directly to the result
            # This includes strings, numbers, booleans, and lists
            result[full_key] = value
    
    # Return the flattened dictionary
    return result


def parse_yaml(file_path):
    """
    Parse a YAML file and return a flat dictionary of its contents.
    
    Handles MULTI-DOCUMENT YAML files (common in Kubernetes manifests,
    Helm output, and Docker Compose files). Each document is separated
    by `---` and may contain unrelated resources.
    
    Args:
        file_path: The path to the YAML file
    
    Returns:
        A flat dictionary with dot-separated keys.
        Returns an empty dictionary if the file cannot be parsed.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            # safe_load_all() returns a generator of documents
            # This handles both single-document AND multi-document YAML
            documents = list(yaml.safe_load_all(file))
        
        # Merge all documents into one flat dictionary
        merged = {}
        for idx, doc in enumerate(documents):
            # Skip empty documents (e.g., from trailing ---)
            if doc is None:
                continue
            
            # Only process dict documents
            if not isinstance(doc, dict):
                continue
            
            # Build a unique prefix so documents with the same keys
            # (like 'metadata', 'spec') don't overwrite each other
            kind = doc.get("kind", f"doc{idx}")
            
            metadata = doc.get("metadata", {})
            if isinstance(metadata, dict):
                name = metadata.get("name", f"doc{idx}")
            else:
                name = f"doc{idx}"
            
            prefix = f"{kind}/{name}"
            
            # Flatten this document with the prefix and merge
            flattened = flatten_dictionary(doc, parent_key=prefix)
            merged.update(flattened)
        
        return merged
        
    except yaml.YAMLError as e:
        # Print the error instead of silently swallowing it
        print(f"  [YAML ERROR] {file_path}: {e}")
        return {}
    except (IOError, UnicodeDecodeError) as e:
        print(f"  [IO ERROR] {file_path}: {e}")
        return {}


def parse_json(file_path):
    """
    Parse a JSON file and return a flat dictionary of its contents.
    
    JSON is commonly used for configuration in:
    - Node.js applications (package.json)
    - Web application settings
    - API configurations
    
    Args:
        file_path: The path to the JSON file
    
    Returns:
        A flat dictionary with dot-separated keys.
        Returns an empty dictionary if the file cannot be parsed.
    
    Example:
        # If config.json contains:
        # {"server": {"timeout": 30}}
        #
        # parse_json("config.json") returns:
        # {"server.timeout": 30}
    """
    try:
        # Open the file in read mode with UTF-8 encoding
        with open(file_path, "r", encoding="utf-8") as file:
            # json.load() parses the JSON content into a Python dictionary
            data = json.load(file)
        
        # Flatten the nested dictionary into a flat one
        return flatten_dictionary(data)
    except (json.JSONDecodeError, IOError, UnicodeDecodeError):
        # If the file is not valid JSON or cannot be read, return empty dict
        return {}


def parse_properties(file_path):
    """
    Parse a Java properties file and return a flat dictionary.
    
    Properties files have a simple format:
    key=value
    another.key=another value
    
    They are commonly used in Java applications for configuration.
    
    Args:
        file_path: The path to the properties file
    
    Returns:
        A flat dictionary with the keys and values from the file.
        Returns an empty dictionary if the file cannot be parsed.
    
    Example:
        # If config.properties contains:
        # server.timeout=30
        # retry.attempts=3
        #
        # parse_properties("config.properties") returns:
        # {"server.timeout": "30", "retry.attempts": "3"}
    """
    # Create an empty dictionary to store our results
    result = {}
    
    try:
        # Open the file in read mode with UTF-8 encoding
        with open(file_path, "r", encoding="utf-8") as file:
            # Loop through each line in the file
            for line in file:
                # Remove leading and trailing whitespace
                line = line.strip()
                
                # Skip empty lines and comment lines (starting with # or !)
                if not line or line.startswith("#") or line.startswith("!"):
                    continue
                
                # Split the line at the first '=' or ':' character
                # We check for '=' first because it's more common
                if "=" in line:
                    key, value = line.split("=", 1)
                elif ":" in line:
                    key, value = line.split(":", 1)
                else:
                    # If there's no '=' or ':', skip this line
                    continue
                
                # Remove whitespace from the key and value
                key = key.strip()
                value = value.strip()
                
                # Add the key-value pair to our result dictionary
                result[key] = value
    except (IOError, UnicodeDecodeError):
        # If the file cannot be read, return empty dict
        return {}
    
    # Return the parsed properties
    return result


def parse_xml(file_path):
    """
    Parse an XML file and return a flat dictionary of its contents.
    
    XML is used for configuration in:
    - Java applications (web.xml, pom.xml)
    - .NET applications (app.config)
    - Various enterprise systems
    
    Args:
        file_path: The path to the XML file
    
    Returns:
        A flat dictionary with dot-separated keys.
        Returns an empty dictionary if the file cannot be parsed.
    
    Example:
        # If config.xml contains:
        # <config>
        #   <server>
        #     <timeout>30</timeout>
        #   </server>
        # </config>
        #
        # parse_xml("config.xml") returns:
        # {"config.server.timeout": "30"}
    """
    # Create an empty dictionary to store our results
    result = {}
    
    try:
        # Parse the XML file into an ElementTree object
        tree = ET.parse(file_path)
        
        # Get the root element of the XML tree
        root = tree.getroot()
        
        # Use a recursive function to walk through the XML tree
        def walk_element(element, prefix=""):
            """
            Recursively walk through an XML element and its children.
            
            Args:
                element: The XML element to process
                prefix: The key prefix built from parent elements
            """
            # Build the current key by combining prefix and element tag
            current_key = f"{prefix}.{element.tag}" if prefix else element.tag
            
            # Check if this element has any child elements
            children = list(element)
            
            if children:
                # If it has children, recursively process each child
                for child in children:
                    walk_element(child, current_key)
            else:
                # If it has no children, it's a leaf node
                # Store its text content as the value
                # Use empty string if there's no text
                result[current_key] = element.text.strip() if element.text else ""
        
        # Start walking from the root element
        walk_element(root)
        
    except (ET.ParseError, IOError, UnicodeDecodeError):
        # If the file is not valid XML or cannot be read, return empty dict
        return {}
    
    # Return the parsed XML
    return result


def parse_config_file(file_path):
    """
    Parse a configuration file based on its extension.
    
    This is the main entry point for parsing configuration files.
    It detects the file type and calls the appropriate parser.
    
    Args:
        file_path: The path to the configuration file
    
    Returns:
        A flat dictionary with the configuration settings.
        Returns an empty dictionary if the file type is not supported
        or if the file cannot be parsed.
    
    Example:
        # Parse a YAML file
        settings = parse_config_file("config.yaml")
        
        # Parse a JSON file
        settings = parse_config_file("config.json")
    """
    # Get the file extension (without the dot, in lowercase)
    extension = Path(file_path).suffix.lower().lstrip(".")
    
    # Choose the appropriate parser based on the extension
    if extension in ("yml", "yaml"):
        # YAML files: use the YAML parser
        return parse_yaml(file_path)
    elif extension == "json":
        # JSON files: use the JSON parser
        return parse_json(file_path)
    elif extension == "properties":
        # Properties files: use the properties parser
        return parse_properties(file_path)
    elif extension == "xml":
        # XML files: use the XML parser
        return parse_xml(file_path)
    else:
        # Unknown file type: return empty dictionary
        # This shouldn't happen if we check is_config_file() first
        return {}


def find_config_changes(old_config, new_config):
    """
    Compare two configuration dictionaries and find what changed.
    
    This function takes the old and new versions of a configuration
    and returns a dictionary showing only the settings that changed.
    
    Args:
        old_config: Dictionary with the old configuration settings
        new_config: Dictionary with the new configuration settings
    
    Returns:
        A dictionary where each key is a setting that changed,
        and the value is a dictionary with "old" and "new" values.
    
    Example:
        old = {"server.timeout": 30, "retry.attempts": 3}
        new = {"server.timeout": 60, "retry.attempts": 3}
        changes = find_config_changes(old, new)
        # changes is now {"server.timeout": {"old": 30, "new": 60}}
    """
    # Create an empty dictionary to store the changes
    changes = {}
    
    # Get all unique keys from both old and new configurations
    # The | operator creates a union of two sets
    all_keys = set(old_config.keys()) | set(new_config.keys())
    
    # Loop through each key
    for key in all_keys:
        # Get the value from old config (None if key doesn't exist)
        old_value = old_config.get(key)
        
        # Get the value from new config (None if key doesn't exist)
        new_value = new_config.get(key)
        
        # Check if the values are different
        if old_value != new_value:
            # If they're different, record the change
            changes[key] = {
                "old": old_value,   # The value before the change
                "new": new_value,   # The value after the change
            }
    
    # Return the dictionary of changes
    return changes


def extract_config_terms(changes):
    """
    Extract searchable terms from configuration changes.
    
    This function takes the output of find_config_changes() and extracts
    all the words that can be used to match against test files.
    
    Args:
        changes: Dictionary from find_config_changes()
    
    Returns:
        A set of lowercase words extracted from the changed settings.
    
    Example:
        changes = {"server.timeout": {"old": 30, "new": 60}}
        terms = extract_config_terms(changes)
        # terms contains: {"server", "timeout", "server.timeout", "30", "60"}
    """
    # Import the extract_words function from file_utils
    from analyzer.file_utils import extract_words
    
    # Create an empty set to store all the terms
    terms = set()
    
    # Loop through each changed setting
    for key, values in changes.items():
        # Extract words from the setting name (e.g., "server.timeout")
        terms.update(extract_words(key))
        
        # Extract words from the old value (converted to string)
        terms.update(extract_words(str(values["old"])))
        
        # Extract words from the new value (converted to string)
        terms.update(extract_words(str(values["new"])))
    
    # Return the set of all extracted terms
    return terms

def extract_changed_config_keys(old_config, new_config):
    """
    Return the set of keys whose values differ between two configs.
    This works on the flattened dicts produced by parse_config_file().
    """
    changes = {}
    all_keys = set(old_config.keys()) | set(new_config.keys())
    for key in all_keys:
        old_val = old_config.get(key)
        new_val = new_config.get(key)
        if old_val != new_val:
            changes[key] = {"old": old_val, "new": new_val}
    return changes

def services_in_changed_keys(changed_keys):
    """
    Given the set of changed config keys, return the set of service names
    that appear in those keys. Only the services whose blocks changed
    should be affected.
    """
    services = set()
    for key in changed_keys:
        # Keys look like: "Deployment/shippingservice.spec.template..."
        # Extract the part after "Deployment/" or "Service/"
        for prefix in ("Deployment/", "Service/", "StatefulSet/"):
            if prefix in key:
                rest = key.split(prefix, 1)[1]
                service_name = rest.split(".", 1)[0]
                if service_name:
                    services.add(service_name)
    return services