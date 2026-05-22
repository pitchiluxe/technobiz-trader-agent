FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user — never run production containers as root
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Install Python dependencies before copying code (layer cache optimisation)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and set ownership in one layer
COPY --chown=appuser:appuser . .

# Create writable directories the app needs
RUN mkdir -p logs && chown -R appuser:appuser logs

# Drop to non-root user
USER appuser

# Health check — hits /api/status with the auth token from the environment
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -sf http://localhost:${GUI_PORT:-8765}/api/status \
        -H "X-GUI-Token:${GUI_SECRET_KEY}" || exit 1

EXPOSE 8765

# Use exec form so signals (SIGTERM) reach the Python process directly
CMD ["python", "gui_server.py"]
