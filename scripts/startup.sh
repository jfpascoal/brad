#!/bin/bash
# This script is used to start the PostgreSQL container and initialize the database schema for the Bread application.

# Startup script for the Bread application
CONTAINER_NAME="bread-db-1"

# Get db name and user from secrets files
DB_NAME=$(< ./docker/secrets/postgres_db.txt)
DB_USER=$(< ./docker/secrets/postgres_user.txt)

# Check if DB container is running; if not, start it
if [ "$(docker ps -q -f name=${CONTAINER_NAME})" ]; then
    echo "Database container is already running."
else
    # Run docker-compose to start the DB
    docker-compose -f ./docker/docker-compose.yml up -d
    # Wait for the Postgres server to be ready
    echo "Waiting for the Postgres server to be ready..."
    while ! docker exec ${CONTAINER_NAME} pg_isready -U ${DB_USER}; do
        sleep 1
    done
    echo "Postgres server is ready."
fi

# Initialize the database schema
echo "Check if the database is initialized..."


if docker exec ${CONTAINER_NAME} psql -U ${DB_USER} -d ${DB_NAME} \
        -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';" | grep -q 0; then
    echo "Initializing the database schema..."
    python ./src/bread/main.py db_init
    if [ $? -ne 0 ]; then
        echo "Failed to initialize the database schema."
        exit 1
    else
        echo "Database schema initialized successfully."
    fi
else
    echo "Database is already initialized."
fi

echo "Startup complete."
