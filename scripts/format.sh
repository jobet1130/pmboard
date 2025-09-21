#!/bin/bash

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR/.."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required tools
check_requirements() {
    local missing=()
    for cmd in black isort flake8; do
        if ! command_exists "$cmd"; then
            missing+=("$cmd")
        fi
    done

    if [ ${#missing[@]} -ne 0 ]; then
        echo -e "${RED}Error: The following tools are missing:"
        printf ' - %s\n' "${missing[@]}"
        echo -e "Install them with: pip install black isort flake8${NC}"
        exit 1
    fi
}

# Run isort to sort imports
run_isort() {
    echo -e "\n${YELLOW}Running isort to sort imports...${NC}"
    isort "$PROJECT_DIR"
}

# Run black to format code
run_black() {
    echo -e "\n${YELLOW}Running black to format code...${NC}"
    black "$PROJECT_DIR"
}

# Run flake8 for linting
run_flake8() {
    echo -e "\n${YELLOW}Running flake8 for linting...${NC}"
    flake8 "$PROJECT_DIR"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}No linting issues found!${NC}"
    else
        echo -e "${YELLOW}Some linting issues were found. Please review them.${NC}"
    fi
}

# Main function
main() {
    check_requirements
    
    echo -e "${GREEN}Starting code formatting...${NC}"
    
    run_isort
    run_black
    run_flake8
    
    echo -e "\n${GREEN}Formatting complete!${NC}"
}

# Run the script
main "$@"