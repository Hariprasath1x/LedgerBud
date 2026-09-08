#!/bin/bash

# LedgerBud Startup Script for Mac/Linux
# This script delegates to start_servers.py to properly manage processes
# and ensure everything closes cleanly on Ctrl+C.

# Change to the directory where the script is located
cd "$(dirname "$0")"

echo "Activating virtual environment if it exists..."
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Run the python script to start the servers
python3 start_servers.py
