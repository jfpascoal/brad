#!/bin/bash
# This script gracefully stops the PostgreSQL container.

CONTAINER_NAME="bread-db-1"

# Stop the PostgreSQL container
if docker exec ${CONTAINER_NAME} pg_isready -U postgres; then
    echo "Stopping the PostgreSQL container..."
    docker exec -u postgres ${CONTAINER_NAME} pg_ctl stop -m smart
    sleep 1
    while [ "$(docker ps -q -f name=${CONTAINER_NAME})" ]; do
        echo "Waiting for PostgreSQL container to stop..."
        sleep 1
    done
    echo "PostgreSQL container stopped."
else
    echo "PostgreSQL container is not running."
fi

echo "Shutdown complete."