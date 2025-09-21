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

# Function to create superuser
create_superuser() {
    local username="$1"
    local email="$2"
    local password="$3"
    
    # Run Django's createsuperuser command
    if [ -n "$username" ] && [ -n "$email" ] && [ -n "$password" ]; then
        # Non-interactive mode
        echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('$username', '$email', '$password')" | python manage.py shell
    else
        # Interactive mode
        python manage.py createsuperuser
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -u|--username)
            username="$2"
            shift 2
            ;;
        -e|--email)
            email="$2"
            shift 2
            ;;
        -p|--password)
            password="$2"
            shift 2
            ;;
        *)
            echo "Unknown parameter: $1"
            exit 1
            ;;
    esac
done

# Check if all required arguments are provided for non-interactive mode
if { [ -n "$username" ] || [ -n "$email" ] || [ -n "$password" ]; } && 
   { [ -z "$username" ] || [ -z "$email" ] || [ -z "$password" ]; }; then
    echo "Error: When providing any of username, email, or password, you must provide all three."
    echo "Usage: $0 [--username USERNAME] [--email EMAIL] [--password PASSWORD]"
    exit 1
fi

# Create superuser
create_superuser "$username" "$email" "$password"