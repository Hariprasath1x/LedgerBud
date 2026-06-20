#!/bin/bash
set -e

echo "Running database initialization and migrations..."
# This will create tables and seed default data based on app/seeder.py
flask create-db

echo "Starting LedgerBud application..."
exec python run.py
