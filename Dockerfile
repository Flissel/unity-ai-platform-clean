# Unity AI Production Dockerfile
# Multi-stage build for optimized production deployment

# Build stage
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILDPLATFORM
ARG TARGETPLATFORM
ARG BUILDARCH
ARG TARGETARCH

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app/n8n-playground

# Copy dependency files
COPY pyproject.toml ./
COPY n8n-playground/requirements.txt ./

# Install dependencies using pip
RUN pip install --no-cache-dir -r requirements.txt || \
    pip install --no-cache-dir -e .

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH" \
    ENVIRONMENT=production

# Create non-root user
RUN groupadd -r unityai && useradd -r -g unityai unityai

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code (only if exists)
COPY pyproject.toml ./
# Create placeholder directories for missing components

# Copy application files
COPY n8n-playground/ ./


# Create necessary directories
RUN mkdir -p /app/logs /app/uploads /app/temp \
    && chown -R unityai:unityai /app

# Switch to non-root user
USER unityai

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--access-log"]

# Development stage
FROM production as development

# Switch back to root for development tools
USER root

# Install development dependencies
RUN apt-get update && apt-get install -y \
    git \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Install development dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


# Switch back to unityai user
USER unityai

# Development command with hot reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "debug"]

# Testing stage (for CI/CD only - not used in production)
FROM development as testing

# Switch to root for test setup
USER root

# Install additional test dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Switch back to unityai user
USER unityai

# Run tests
CMD ["python", "-m", "pytest", "-v", "--cov=src", "--cov-report=html", "--cov-report=term-missing"]

# Production stage (final stage - this will be the default)
FROM production as final

# This ensures production is the default target when no --target is specified