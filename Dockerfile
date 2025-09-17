# Multi-stage build for optimized production image
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Create non-root user for security
RUN groupadd -r botuser && useradd -r -g botuser botuser

# Set working directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/botuser/.local

# Copy application code
COPY src/ ./src/
COPY requirements.txt .

# Set ownership and permissions
RUN chown -R botuser:botuser /app
USER botuser

# Set Python path
ENV PATH=/home/botuser/.local/bin:$PATH
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import asyncio; from src.bot import bot_app; print('OK')" || exit 1

# Expose port
EXPOSE 8443

# Run application
CMD ["python", "src/main.py"]