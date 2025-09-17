#!/bin/bash

# Docker wrapper for mypy checks
# Usage:
#   ./docker_mypy.sh                    # Check against baseline
#   ./docker_mypy.sh --generate         # Generate new baseline
#   ./docker_mypy.sh --shell            # Open interactive shell

set -e

# Set user ID and group ID for consistent file permissions
export USER_ID=$(id -u)
export GROUP_ID=$(id -g)

# Build the image if it doesn't exist or if Dockerfile changed
echo "🔨 Building Docker image (if needed)..."
docker compose build mypy-check

case "${1:-}" in
    --generate)
        docker compose run --rm mypy-generate
        ;;
    --shell)
        echo "🐚 Opening interactive shell in Docker container..."
        docker compose run --rm cli
        ;;
    "")
        docker compose run --rm mypy-check
        ;;
    *)
        echo "Usage: $0 [--generate|--shell]"
        echo ""
        echo "Options:"
        echo "  --generate    Generate a new mypy baseline file"
        echo "  --shell       Open interactive shell in container"
        echo "  (no args)     Check current mypy output against baseline"
        exit 1
        ;;
esac
