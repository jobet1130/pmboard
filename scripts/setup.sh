#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
PYTHON_CMD="python3"
PIP_CMD="pip3"

# Check if virtual environment exists, if not create it
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    $PYTHON_CMD -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment."
        exit 1
    fi
else
    echo -e "${GREEN}Virtual environment already exists.${NC}"
fi

# Activate virtual environment
echo -e "\n${YELLOW}Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo -e "\n${YELLOW}Upgrading pip...${NC}"
$PYTHON_CMD -m pip install --upgrade pip

# Install dependencies
echo -e "\n${YELLOW}Installing dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    $PIP_CMD install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Failed to install dependencies."
        exit 1
    fi
else
    echo "requirements.txt not found. No dependencies to install."
fi

# Run migrations
echo -e "\n${YELLOW}Running migrations...${NC}"
$PYTHON_CMD manage.py migrate --noinput
if [ $? -ne 0 ]; then
    echo "Failed to run migrations."
    exit 1
fi

# Collect static files
echo -e "\n${YELLOW}Collecting static files...${NC}"
$PYTHON_CMD manage.py collectstatic --noinput
if [ $? -ne 0 ]; then
    echo "Failed to collect static files."
    exit 1
fi

echo -e "\n${GREEN}Setup completed successfully!${NC}"
echo -e "To activate the virtual environment, run:"
echo -e "source $VENV_DIR/bin/activate"