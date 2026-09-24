# =============================================================================
# SETUP SCRIPT
# This file allows the project to be installed as a Python package.
# You can run: pip install -e .  to install it in development mode.
# =============================================================================

from setuptools import setup, find_packages

# Read the contents of the README file for the long description
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Define the package configuration
setup(
    # The name of the package
    name="test-impact-analyzer",
    
    # The version of the package
    version="1.0.0",
    
    # A short description
    description="A configuration-aware test impact analyzer for microservices",
    
    # A long description (from README.md)
    long_description=long_description,
    long_description_content_type="text/markdown",
    
    # The author's name
    author="Your Name",
    
    # The author's email
    author_email="your.email@example.com",
    
    # The URL of the project
    url="https://github.com/yourusername/test-impact-analyzer",
    
    # Automatically find all packages in the project
    packages=find_packages(),
    
    # The Python version required
    python_requires=">=3.10",
    
    # The dependencies required to run the package
    install_requires=[
        "PyYAML>=6.0",
        "opentelemetry-api>=1.20.0",
        "opentelemetry-sdk>=1.20.0",
    ],
    
    # Classification metadata
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)