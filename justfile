# Set the default shell to sh (standard for Git Bash)
set shell := ["sh", "-c"]

# List available commands
default:
    @just --list

# Install dependencies and sync the virtual environment
setup:
    @echo "Setting up the local environment..."
    uv sync
    @echo "Setup complete. Virtual environment is ready."

# Start the database container and initialize the schema
up:
    @echo "Starting the database container..."
    docker-compose -f docker/docker-compose.yml up -d
    @echo "Waiting for the Postgres server to be ready..."
    @while ! docker exec brad-db-1 pg_isready -U postgres > /dev/null 2>&1; do sleep 1; done
    @echo "Initializing the database schema..."
    uv run brad db init
    @echo "Startup complete."

# Stop the database container
down:
    @echo "Stopping the database container..."
    docker-compose -f docker/docker-compose.yml stop
    @echo "Container stopped."

# Run code formatting
fmt:
    uv run ruff format src/ tests/

# Run code linting/checks
check:
    uv run ruff check src/ tests/
