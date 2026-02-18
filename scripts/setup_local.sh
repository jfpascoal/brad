#!/bin/bash
# This script sets up the local environment to run the Brad application, including:
# 1) create virtual environment (remove existing one if it exists)
# 2) install dependencies
# 3) build the application

echo "Setting up the local environment..."
python -m pip install --upgrade pip setuptools

# Create virtual environment
if [[ -d "./.venv" ]]; then
    echo "Removing existing virtual environment..."
    rm -rf ./.venv
fi
echo "Creating a new virtual environment..."
python -m venv ./.venv
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windows
    source .venv/Scripts/activate
else
    # Unix-like systems
    source .venv/bin/activate
fi

# Install dependencies and build
echo "Installing dependencies and building..."
uv sync

echo "Setup complete."