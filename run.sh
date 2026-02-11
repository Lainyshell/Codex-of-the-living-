#!/bin/bash

# Treasury API Run Script
# This script provides a simple way to run the Flask application

set -e

echo "======================================"
echo "Treasury API - Starting Application"
echo "======================================"
echo ""

# Check if we're in the correct directory
if [ ! -f "app/main.py" ]; then
    echo "Error: app/main.py not found. Please run this script from the repository root."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.11 or later."
    exit 1
fi

echo "Python version:"
python3 --version
echo ""

# Navigate to the app directory
cd app

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "Error: requirements.txt not found in app directory."
    exit 1
fi

# Check if requirements are installed
echo "Checking dependencies..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Installing required dependencies..."
    pip3 install -r requirements.txt
else
    echo "Dependencies already installed."
fi
echo ""

# Run the application
echo "Starting Flask application on http://0.0.0.0:5000"
echo "Press Ctrl+C to stop the server"
echo ""
echo "Available endpoints:"
echo "  - http://localhost:5000/       (Status endpoint)"
echo "  - http://localhost:5000/rates  (Treasury rates endpoint)"
echo ""

python3 main.py
