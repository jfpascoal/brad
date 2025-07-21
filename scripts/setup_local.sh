#!/bin/bash
# This script sets up the local environment to run the Bread application, including:
# 1) create virtual environment
# 2) install dependencies
# 3) build the application

echo "Setting up the local environment..."

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv development

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Build the application
echo "Building the application..."
pip install -e .

echo "Setup complete."