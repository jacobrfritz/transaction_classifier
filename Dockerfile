FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files and README (required for metadata)
COPY pyproject.toml uv.lock README.md ./

# Install dependencies (including api extra)
# Use --no-install-project to cache dependencies without the source code
# We use a cache mount for uv to speed up subsequent builds
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# Pre-download the ML model BEFORE copying source code
# This ensures that code changes don't trigger a model redownload.
# We also cache the huggingface/torch directory to avoid redownloads if the layer invalidates
RUN --mount=type=cache,target=/root/.cache/huggingface \
    /app/.venv/bin/python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy source code
COPY src ./src

# Install the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV DATABASE_URL=postgresql+psycopg://admin:password@db:5432/transactions_db

# Expose port
EXPOSE 8000

# Run the application
CMD ["/app/.venv/bin/python", "-m", "uvicorn", "transaction_classifier.app:app", "--host", "0.0.0.0", "--port", "8000"]
