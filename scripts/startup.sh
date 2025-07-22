#!/bin/bash
# This script is used to start the PostgreSQL container and initialize the database schema for the Brad application.

# Startup script for the Brad application
CONTAINER_NAME="brad-db-1"
DOCKER_DIR="./docker"
SECRETS_DIR=${DOCKER_DIR}"/secrets"

# Get db name and user from secrets files
DB_NAME=$(< ${SECRETS_DIR}/postgres_db.txt) && \
DB_USER=$(< ${SECRETS_DIR}/postgres_user.txt)

# Check if Docker desktop is running
if ! docker desktop status >/dev/null 2>&1; then
    docker desktop start
    if [ $? -ne 0 ]; then
        echo "Failed to start Docker Desktop. Please ensure Docker is installed and running."
        exit 1
    fi
    echo "Docker Desktop started successfully."
fi

# Check if DB container is running; if not, start it
if [ "$(docker ps -q -f name=${CONTAINER_NAME})" ]; then
    echo "Database container is already running."
else
    # Run docker-compose to start the DB
    docker-compose -f ${DOCKER_DIR}/docker-compose.yml up -d
    # Wait for the Postgres server to be ready
    echo "Waiting for the Postgres server to be ready..."
    while ! docker exec "${CONTAINER_NAME}" pg_isready -U "${DB_USER}"; do
        sleep 1
    done
    echo "Postgres server is ready."
fi

# Initialize the database schema
if docker exec "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}" \
        -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';" | grep -q 0; then
    echo "Initializing the database schema..."
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        # Windows
        source .venv/Scripts/activate
    else
        # Unix-like systems
        source .venv/bin/activate
    fi
    python ./python/src/brad/main.py db_init
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
