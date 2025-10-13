#!/usr/bin/env bash
# install.sh: Sets up virtual environment and installs dependencies

# Create virtual environment
uv sync

# Activate
source .venv/bin/activate

