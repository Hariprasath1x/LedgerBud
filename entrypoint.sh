#!/bin/bash
set -e

if [ "$SERVICE_TYPE" = "backend" ] || [ -n "$PORT" ]; then
    echo "Starting LedgerBud FastAPI Backend on port ${PORT:-8000}..."
    exec python run_fastapi.py
elif [ "$SERVICE_TYPE" = "frontend" ]; then
    echo "Starting LedgerBud Streamlit Frontend on port ${PORT:-8501}..."
    exec streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port "${PORT:-8501}" --server.headless true
else
    echo "Starting LedgerBud local all-in-one servers..."
    exec python start_servers.py
fi
