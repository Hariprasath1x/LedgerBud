@echo off
REM LedgerBud Startup Script
REM This script delegates to start_servers.py to properly manage processes
REM and ensure everything closes cleanly on Ctrl+C.

echo Activating virtual environment if it exists...
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

python start_servers.py
