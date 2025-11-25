# ============================================================================
# OptiFlow Simulator - Dockerfile
# ============================================================================
#
# Virtual PLC Simulator with OPC-UA server
#
# Build:
#   docker build -t optiflow-simulator:latest ./simulator
#
# Run:
#   docker run -p 4840:4840 -p 4850:4850 optiflow-simulator:latest
#
# Ports:
#   4840 - OPC-UA server (Gateway connects here)
#   4850 - REST API (Control interface)
# ============================================================================

FROM python:3.11-slim

LABEL maintainer="OptiFlow Team"
LABEL description="OptiFlow Virtual PLC Simulator (Grain Terminal)"
LABEL version="1.0.0"

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose ports
EXPOSE 4840
EXPOSE 4850

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:4850/health')" || exit 1

# Run simulator
CMD ["python", "-m", "app.main"]
