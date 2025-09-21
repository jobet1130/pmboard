#!/bin/bash

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR/.."

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to build and start containers
start_containers() {
    echo "Building and starting containers..."
    docker-compose -f "$PROJECT_DIR/docker-compose.yml" up -d --build
}

# Function to run migrations
run_migrations() {
    echo "Running database migrations..."
    docker-compose -f "$PROJECT_DIR/docker-compose.yml" exec web python manage.py migrate --noinput
}

# Function to show container status
show_status() {
    echo -e "\nContainer status:"
    docker-compose -f "$PROJECT_DIR/docker-compose.yml" ps
}

# Main execution
check_docker
start_containers
run_migrations
show_status

echo -e "\nContainers are up and running!"
echo "Access the application at http://localhost:8000"