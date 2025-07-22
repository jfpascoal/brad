#!/bin/bash
# This script sets up the local environment to run the Brad application, including:
# 1) create virtual environment
# 2) install dependencies
# 3) build the application

echo "Setting up the local environment..."

# Create virtual environment
echo "Creating virtual environment..."
python -m venv ./.venv
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windows
    source .venv/Scripts/activate
else
    # Unix-like systems
    source .venv/bin/activate
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r .python/requirements.txt

# Build the application
echo "Building the application..."
pip install -e ./python

echo "Setup complete."