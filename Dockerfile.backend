# ==============================================================================
# Production Dockerfile for Thai ID Card OCR & KIE Backend Service (FastAPI)
# ==============================================================================
FROM python:3.12-slim

# Prevent writing bytecode and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install essential system dependencies (curl for healthcheck, ca-certificates)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for caching layers
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user for security best practices
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Copy application source code and test suite
COPY --chown=appuser:appuser app/ ./app
COPY --chown=appuser:appuser tests/ ./tests

USER appuser

EXPOSE 8000

# Container healthcheck using FastAPI health endpoint
HEALTHCHECK --interval=20s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start Uvicorn ASGI server with production workers
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
