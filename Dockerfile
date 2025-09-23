# Use Python 3.12 slim image for smaller size
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies and uv
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install Python dependencies with uv
RUN uv sync --group dev --group telegram --frozen

# Create a non-root user for security first
RUN useradd --create-home --shell /bin/bash app

# Copy the rest of the application
COPY . .

# Ensure proper ownership and permissions
RUN chown -R app:app /app && \
    mkdir -p /app/.mypy_cache && \
    chown -R app:app /app/.mypy_cache

USER app

# Default command runs mypy check
CMD ["./scripts/check_mypy.sh"]
