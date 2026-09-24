# =============================================================================
# TRACING MODULE
# This module contains helper functions for tracing test execution and
# recording configuration access. It provides a simple API for tests
# to record which configuration settings they use.
# =============================================================================

from contextlib import contextmanager
from analyzer.telemetry import get_tracer


# Global selector instance that records config access during tests
# This is used by the record_config_access function
_selector = None


def get_selector():
    """
    Get the global ConfigurationAwareSelector instance.
    
    If no selector exists yet, create one.
    
    Returns:
        The global selector instance.
    
    Example:
        selector = get_selector()
        # selector is now available for recording and selecting
    """
    global _selector
    
    # If we don't have a selector yet, create one
    if _selector is None:
        # Import here to avoid circular imports
        from analyzer.selector import ConfigurationAwareSelector
        _selector = ConfigurationAwareSelector()
    
    # Return the selector
    return _selector


def reset_selector():
    """
    Reset the global selector, clearing all recorded dependencies.
    
    This is useful between test runs to ensure we start fresh.
    
    Example:
        reset_selector()
        # Now the selector has no recorded dependencies
    """
    global _selector
    _selector = None


@contextmanager
def trace_test(test_id):
    """
    Create a context manager that traces a test execution.
    
    This context manager creates a span for the test, which allows
    us to see what happens during the test in our tracing system.
    
    Args:
        test_id: A unique identifier for the test
    
    Yields:
        The span object created for this test.
    
    Example:
        with trace_test("TestCheckout"):
            # Code here runs with tracing active
            # Any config access will be recorded
            pass
    """
    # Get the global tracer
    tracer = get_tracer()
    
    # If tracing isn't configured, just yield None
    if tracer is None:
        yield None
        return
    
    # Create a span for this test
    # The span name includes the test ID for easy identification
    with tracer.start_as_current_span(f"test:{test_id}") as span:
        # Add an attribute to the span with the test ID
        span.set_attribute("test.id", test_id)
        
        # Yield the span to the caller
        yield span


def record_config_access(test_id, config_key):
    """
    Record that a test accessed a specific configuration setting.
    
    This function is called whenever a test reads a configuration value.
    It records the access in the global selector.
    
    Args:
        test_id: The identifier of the test
        config_key: The configuration setting that was accessed
    
    Example:
        record_config_access("TestCheckout", "server.timeout")
        # Now the selector knows TestCheckout uses server.timeout
    """
    # Get the global selector
    selector = get_selector()
    
    # Record the access
    selector.record_config_access(test_id, config_key)


def get_config(test_id, config, key):
    """
    Read a configuration value and record that it was accessed.
    
    This is a wrapper around dictionary access that also records
    the access in our tracing system. Tests should use this function
    instead of directly accessing configuration dictionaries.
    
    Args:
        test_id: The identifier of the test reading the config
        config: The configuration dictionary
        key: The key to read from the dictionary
    
    Returns:
        The value associated with the key in the config dictionary.
    
    Raises:
        KeyError: If the key is not found in the config dictionary.
    
    Example:
        config = {"server.timeout": 30}
        value = get_config("TestCheckout", config, "server.timeout")
        # value is 30, and the access is recorded
    """
    # Record that this test accessed this configuration setting
    record_config_access(test_id, key)
    
    # Return the value from the configuration dictionary
    return config[key]


def get_test_dependencies(test_id):
    """
    Get the configuration settings used by a specific test.
    
    Args:
        test_id: The identifier of the test
    
    Returns:
        A set of configuration setting names used by the test.
    
    Example:
        deps = get_test_dependencies("TestCheckout")
        # deps might be {"server.timeout", "retry.attempts"}
    """
    # Get the global selector
    selector = get_selector()
    
    # Return the dependencies for this test
    return selector.get_test_dependencies(test_id)


def select_affected_tests(changed_settings):
    """
    Select tests that are affected by specific configuration changes.
    
    Args:
        changed_settings: A list of configuration setting names that changed
    
    Returns:
        A list of dictionaries, each containing "test" and "settings" keys.
    
    Example:
        affected = select_affected_tests(["server.timeout"])
        # affected might be:
        # [{"test": "TestCheckout", "settings": ["server.timeout"]}]
    """
    # Get the global selector
    selector = get_selector()
    
    # Select affected tests
    return selector.select_tests(changed_settings)