# syntax=docker/dockerfile:1.7
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv from the official single-binary installer.
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && ln -s /root/.local/bin/uv /usr/local/bin/uv

WORKDIR /app

# Install prod deps first (cache-friendly).
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application source and rebuild the versioned SQLite files so the image
# always ships a consistent data layer.
COPY app ./app
COPY scripts ./scripts
RUN uv sync --frozen --no-dev
RUN uv run python -m scripts.build_data

ENV PORT=8000
EXPOSE 8000

# Render overrides $PORT at runtime; fall back to 8000 for local docker runs.
CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
