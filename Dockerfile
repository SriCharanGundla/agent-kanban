# Backend Dockerfile for agent-kanban
# Uses uv for fast, reproducible Python dependency management

FROM ghcr.io/astral-sh/uv:0.5.14-python3.12-bookworm-slim

WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./
COPY .python-version ./

# Install dependencies using uv
# --frozen ensures reproducible builds
# --no-dev excludes development dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Expose port 8000 (mapped to 7655 on host by deploy script)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').getcode()" || exit 1

# Run the FastAPI server
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
