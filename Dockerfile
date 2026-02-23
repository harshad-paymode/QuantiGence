# Dockerfile
# Multi-stage build tuned for your local/dev workflow (Poetry 2.2.1 + Python 3.11.9)

#######################
# builder stage
#######################
FROM python:3.11.9-slim AS builder

# Configure Poetry environment & path
ENV POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR="/tmp/poetry_cache" \
    PATH="/opt/poetry/bin:$PATH"

# Install system deps needed to build wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl git libpq-dev gcc ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# Install a pinned Poetry version (you said 2.2.1)
RUN pip install "poetry==2.2.1"

WORKDIR /app

# Copy lock files first to leverage Docker cache
COPY pyproject.toml poetry.lock ./

# Install dependencies (only main - adjust if you need dev extras)
RUN poetry install --no-root --only main

# Copy application sources
COPY . .

#######################
# runtime stage
#######################
FROM python:3.11.9-slim

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR="/tmp/poetry_cache" \
    PATH="/opt/poetry/bin:$PATH"

# Minimal packages for runtime
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# Create non-root user for safety
RUN useradd -m appuser || true

WORKDIR /app

# Copy installed packages & app code from builder
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app

# Ensure permissions (appuser owns files)
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Default: start uvicorn. In dev you may override with docker-compose to use --reload.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]