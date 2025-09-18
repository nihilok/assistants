.PHONY: help install install-dev test lint mypy mypy-generate clean build docker-shell format check-all dev-setup

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation targets
install: ## Install package for production
	pip install -e .

install-dev: ## Install package with development dependencies
	pip install -e .[dev]
	pip install -r dev_requirements.txt

# Development targets
dev-setup: install-dev ## Complete development environment setup
	@echo "Development environment setup complete!"
	@echo "You can now run: make mypy, make test, make lint"

# Testing and quality targets (local)
test: ## Run pytest tests
	pytest assistants/tests/ -v

lint: ## Run ruff linting
	ruff check assistants/

format: ## Format code with ruff
	ruff format assistants/

# Testing and quality targets (Docker)
mypy: ## Run mypy type checking against baseline in Docker
	./scripts/docker_wrapper.sh

mypy-generate: ## Generate new mypy baseline in Docker
	./scripts/docker_wrapper.sh --generate

check-all: lint mypy test ## Run all quality checks (lint, mypy, test)

# Build targets
clean: ## Clean build artifacts and cache files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

build: clean ## Build distribution packages
	python -m build

# Docker targets
docker-shell: ## Open interactive shell in Docker container
	./scripts/docker_wrapper.sh --shell

# CLI shortcuts (run in Docker containers)
ai-cli: ## Run ai-cli in Docker container (use: make ai-cli ARGS="--help")
	./scripts/docker_wrapper.sh --cli $(ARGS)

chatgpt: ## Run chatgpt CLI in Docker container
	./scripts/docker_wrapper.sh --cli --provider openai

claude: ## Run claude CLI in Docker container
	./scripts/docker_wrapper.sh --cli --provider anthropic

telegram-bot: ## Run Telegram bot in Docker container
	docker compose run --rm cli ai-tg-bot

# Utility targets
config: ## Show configuration info
	@echo "Python version: $$(python --version)"
	@echo "Pip version: $$(pip --version)"
	@echo "Project location: $$(pwd)"
	@echo "Virtual environment: $${VIRTUAL_ENV:-Not activated}"

# Development workflow shortcuts
quick-check: lint mypy ## Quick development check (lint + mypy, no tests)

full-check: check-all ## Alias for check-all

# Release helpers
version: ## Show current version
	@python -c "from assistants.version import __VERSION__; print(__VERSION__)"

# Examples and demos
example: ## Run the universal assistant demo in Docker
	docker compose run --rm cli python examples/universal_assistant_demo.py
