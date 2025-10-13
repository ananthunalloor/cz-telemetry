@echo off
REM install.bat: Sets up virtual environment and installs dependencies

REM Create virtual environment
uv sync

REM Activate environment
.venv\Scripts\activate

