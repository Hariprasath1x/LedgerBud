#!/bin/bash
set -e

echo "Starting LedgerBud application..."
echo "  Backend API: http://localhost:8000"
echo "  Frontend UI: http://localhost:8501"

exec python start_servers.py
