@echo off
REM start.bat: Activates environment and runs the app

REM Activate virtual environment
.venv\Scripts\activate

REM Run application
uv run main.py