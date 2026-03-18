#!/usr/bin/env bash
# AgriWatch startup script

set -e

echo "=== AgriWatch IoT Agricultural Monitor ==="
echo "Starting on port 8003..."

# Create required directories
mkdir -p instance seed_data

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

echo "Installing dependencies..."
pip install -q -r requirements.txt

echo "Starting AgriWatch..."
python app.py
