#!/bin/bash

# Docker wrapper for mypy checks and CLI
# Usage:
#   ./docker_wrapper.sh                    # Check against baseline
#   ./docker_wrapper.sh --generate         # Generate new baseline
#   ./docker_wrapper.sh --shell            # Open interactive shell
#   ./docker_wrapper.sh --cli [args...]    # Run ai-cli with arguments

set -e

# Build the image if it doesn't exist or if Dockerfile changed
echo "🔨 Building Docker image (if needed)..."
docker compose build mypy-check

case "${1:-}" in
    --generate)
        docker compose run --rm mypy-generate
        ;;
    --shell)
        echo "🐚 Opening interactive shell in Docker container..."
        docker compose run --rm cli bash
        ;;
    --cli)
        shift # Remove --cli from arguments
        echo "🤖 Running ai-cli with arguments: $*"
        docker compose run --rm cli ai-cli "$@"
        ;;
    "")
        docker compose run --rm mypy-check
        ;;
    *)
        echo "Usage: $0 [--generate|--shell|--cli [args...]]"
        echo ""
        echo "Options:"
        echo "  --generate           Generate a new mypy baseline file"
        echo "  --shell              Open interactive shell in container"
        echo "  --cli [args...]      Run ai-cli with the specified arguments"
        echo "  (no args)            Check current mypy output against baseline"
        echo ""
        echo "Examples:"
        echo "  $0 --cli --help                    # Show ai-cli help"
        echo "  $0 --cli --model gpt-4             # Run ai-cli with GPT-4"
        exit 1
        ;;
esac
