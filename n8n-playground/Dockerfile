# n8n API Playground - Production Dockerfile
# Multi-stage build for optimized production deployment

# Build stage
FROM python:3.11-slim as builder

# Set build environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Set production environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    ENVIRONMENT=production

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    libpq5 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/temp && \
    chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Production command without reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4", "--log-level", "info"]