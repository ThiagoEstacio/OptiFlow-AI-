FROM python:3.11-slim

LABEL maintainer="OptiFlow AI <support@optiflow.ai>"
LABEL description="OPC UA Server - Grain Terminal Simulator"

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY server.py .

# Expose OPC UA port
EXPOSE 4840

# Run server
CMD ["python", "-u", "server.py"]
