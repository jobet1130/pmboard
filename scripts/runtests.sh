#!/bin/bash

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/../venv"
PROJECT_DIR="$SCRIPT_DIR/.."

# Activate virtual environment
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
else
    echo "Error: Virtual environment not found at $VENV_DIR"
    exit 1
fi

# Load environment variables from .env if it exists
if [ -f "$SCRIPT_DIR/../.env" ]; then
    export $(grep -v '^#' "$SCRIPT_DIR/../.env" | xargs)
fi

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# Check if pytest is available
if command -v pytest &> /dev/null; then
    # Check if pytest-cov is installed
    if python -c "import pytest_cov" &> /dev/null; then
        echo "Running tests with pytest and coverage..."
        python -m pytest --cov=. --cov-report=term-missing --cov-config=.coveragerc
    else
        echo "Running tests with pytest..."
        python -m pytest
    fi
else
    echo "pytest not found, falling back to Django's test runner..."
    python manage.py test
fi