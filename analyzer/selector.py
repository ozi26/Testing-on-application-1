# =============================================================================
# SELECTOR MODULE
# This module contains the ConfigurationAwareSelector class, which is
# responsible for mapping tests to configuration settings and selecting
# only the tests that are affected by configuration changes.
# =============================================================================

class ConfigurationAwareSelector:
    """
    A class that maps tests to the configuration settings they use,
    and selects affected tests when configuration changes occur.
    
    This is the core innovation of our analyzer - it understands the
    relationship between tests and configuration settings, which
    traditional test impact analysis tools completely miss.
    
    Example:
        selector = ConfigurationAwareSelector()
        
        # Record that TestCheckout uses these settings
        selector.record_config_access("TestCheckout", "server.timeout")
        selector.record_config_access("TestCheckout", "inventory.retry.attempts")
        
        # Record that TestInventory uses this setting
        selector.record_config_access("TestInventory", "inventory.retry.attempts")
        
        # When "inventory.retry.attempts" changes, find affected tests
        affected = selector.select_tests(["inventory.retry.attempts"])
        # affected contains TestCheckout and TestInventory
    """
    
    def __init__(self):
        """
        Initialize the selector with an empty dependency map.
        
        The dependency map is a dictionary where:
        - Keys are test IDs (e.g., "TestCheckout")
        - Values are sets of configuration settings used by that test
        """
        # self.test_dependencies maps test_id -> set of config keys
        self.test_dependencies = {}
    
    def record_config_access(self, test_id, config_key):
        """
        Record that a test accessed a specific configuration setting.
        
        This method is called during test execution whenever a test
        reads a configuration value. It builds up a picture of which
        tests depend on which settings.
        
        Args:
            test_id: A unique identifier for the test (e.g., "TestCheckout")
            config_key: The configuration setting that was accessed
                       (e.g., "server.timeout")
        
        Example:
            selector.record_config_access("TestCheckout", "server.timeout")
        """
        # If this test_id hasn't been seen before, create an empty set for it
        if test_id not in self.test_dependencies:
            self.test_dependencies[test_id] = set()
        
        # Add the config_key to the set of settings used by this test
        self.test_dependencies[test_id].add(config_key)
    
    def get_test_dependencies(self, test_id):
        """
        Get the set of configuration settings used by a specific test.
        
        Args:
            test_id: The identifier of the test
        
        Returns:
            A set of configuration setting names used by the test.
            Returns an empty set if the test hasn't been seen.
        
        Example:
            deps = selector.get_test_dependencies("TestCheckout")
            # deps might be {"server.timeout", "inventory.retry.attempts"}
        """
        # Return the set of settings for this test, or an empty set
        return self.test_dependencies.get(test_id, set())
    
    def get_all_dependencies(self):
        """
        Get the complete dependency map for all tests.
        
        Returns:
            A dictionary mapping test IDs to sets of config settings.
        
        Example:
            all_deps = selector.get_all_dependencies()
            # all_deps might be:
            # {
            #     "TestCheckout": {"server.timeout", "retry.attempts"},
            #     "TestInventory": {"retry.attempts"},
            # }
        """
        # Return a copy of the dependency map
        # We use a copy to prevent external code from modifying our internal state
        return dict(self.test_dependencies)
    
    def select_tests(self, changed_settings):
        """
        Select tests that are affected by specific configuration changes.
        
        This is the main method of the selector. Given a list of
        configuration settings that have changed, it returns all the
        tests that use those settings.
        
        Args:
            changed_settings: A list (or set) of configuration setting names
                             that have changed
        
        Returns:
            A list of dictionaries, where each dictionary contains:
            - "test": The test ID
            - "settings": A sorted list of the affected settings
        
        Example:
            changed = ["inventory.retry.attempts"]
            affected = selector.select_tests(changed)
            # affected might be:
            # [
            #     {"test": "TestCheckout", "settings": ["inventory.retry.attempts"]},
            #     {"test": "TestInventory", "settings": ["inventory.retry.attempts"]},
            # ]
        """
        # Convert changed_settings to a set for faster lookup
        changed_settings = set(changed_settings)
        
        # Create an empty list to store the selected tests
        selected_tests = []
        
        # Loop through each test and its dependencies
        for test_id, dependencies in self.test_dependencies.items():
            # Find which of the changed settings are used by this test
            # The intersection() method returns common elements
            affected_settings = changed_settings.intersection(dependencies)
            
            # If this test uses any of the changed settings, include it
            if affected_settings:
                selected_tests.append({
                    "test": test_id,
                    # Convert to sorted list for consistent output
                    "settings": sorted(affected_settings),
                })
        
        # Return the list of affected tests
        return selected_tests
    
    def clear(self):
        """
        Clear all recorded dependencies.
        
        This method resets the selector to its initial state,
        removing all recorded test-config dependencies.
        
        Example:
            selector.clear()
            # selector.test_dependencies is now {}
        """
        # Reset the dependency map to an empty dictionary
        self.test_dependencies = {}
    
    def __len__(self):
        """
        Return the number of tests that have recorded dependencies.
        
        This allows us to use len(selector) to get the count.
        
        Example:
            selector.record_config_access("Test1", "setting1")
            selector.record_config_access("Test2", "setting2")
            count = len(selector)  # count is 2
        """
        return len(self.test_dependencies)
    
    def __repr__(self):
        """
        Return a string representation of the selector.
        
        This is useful for debugging and printing.
        
        Example:
            print(selector)
            # <ConfigurationAwareSelector: 2 tests, 3 total dependencies>
        """
        # Count the total number of dependencies
        total_deps = sum(len(deps) for deps in self.test_dependencies.values())
        
        # Return a formatted string
        return (
            f"<ConfigurationAwareSelector: "
            f"{len(self.test_dependencies)} tests, "
            f"{total_deps} total dependencies>"
        )