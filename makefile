.PHONY: help install install-dev test lint mypy mypy-generate clean build docker-shell format check-all dev-setup pre-commit

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation targets
install: ## Install package for production
	uv sync

install-dev: ## Install package with development dependencies
	uv sync --dev

# Development targets
dev-setup: install-dev ## Complete development environment setup
	@echo "Development environment setup complete!"
	@echo "You can now run: make mypy, make test, make lint"

# Testing and quality targets (local)
test: ## Run pytest tests
	uv run pytest assistants/tests/ -v

lint: ## Run ruff linting
	uv run ruff check assistants/ --fix

format: ## Format code with ruff
	uv run ruff format assistants/

mypy-generate: ## Generate new mypy baseline in Docker
	./scripts/check_mypy.sh --generate

check-all: lint mypy test ## Run all quality checks (lint, mypy, test)

pre-commit:
	uv run pre-commit run --all-files

# Build targets
clean: ## Clean build artifacts and cache files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

build: clean ## Build distribution packages
	uv build

# Release helpers
version: ## Show current version
	@python -c "from assistants.version import __VERSION__; print(__VERSION__)"

