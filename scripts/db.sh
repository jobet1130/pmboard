#!/bin/bash

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${SCRIPT_DIR}/../backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backups directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Detect database type from environment variables
detect_db_type() {
    if [ -n "$DATABASE_URL" ]; then
        if [[ "$DATABASE_URL" == postgres* ]]; then
            echo "postgres"
        elif [[ "$DATABASE_URL" == sqlite* ]]; then
            echo "sqlite"
        fi
    elif [ -n "$DB_ENGINE" ]; then
        echo "$DB_ENGINE"
    else
        # Default to SQLite if no environment variables are set
        echo "sqlite"
    fi
}

backup_sqlite() {
    local db_file="${1:-db.sqlite3}"
    local backup_file="${BACKUP_DIR}/backup_${TIMESTAMP}.sqlite3"
    cp "$db_file" "$backup_file"
    echo "Backup created at: $backup_file"
}

backup_postgres() {
    local backup_file="${BACKUP_DIR}/backup_${TIMESTAMP}.sql"
    PGPASSWORD=$DB_PASSWORD pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" > "$backup_file"
    echo "Backup created at: $backup_file"
}

restore_sqlite() {
    local backup_file="$1"
    local db_file="${2:-db.sqlite3}"
    cp -f "$backup_file" "$db_file"
    echo "Database restored from: $backup_file"
}

restore_postgres() {
    local backup_file="$1"
    PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f "$backup_file"
    echo "Database restored from: $backup_file"
}

case "$1" in
    backup)
        db_type=$(detect_db_type)
        echo "Creating $db_type backup..."
        "backup_${db_type}" "$2"
        ;;
    restore)
        if [ -z "$2" ]; then
            echo "Error: Please specify a backup file to restore"
            exit 1
        fi
        db_type=$(detect_db_type)
        echo "Restoring $db_type database from $2..."
        "restore_${db_type}" "$2" "$3"
        ;;
    list)
        echo "Available backups:"
        ls -lh "$BACKUP_DIR" | grep -v "total "
        ;;
    *)
        echo "Usage: $0 {backup|restore <filename>|list}"
        exit 1
        ;;
esac