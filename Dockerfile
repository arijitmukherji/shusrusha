# Shusrusha Medical Document Processor - Cross-Platform Docker Container
# Compatible with Windows, macOS, and Linux

FROM python:3.11-slim

# Set environment variables for cross-platform compatibility
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_SERVER_ENABLE_CORS=false

# Set working directory
WORKDIR /app

# Install system dependencies (compatible with both x86 and ARM architectures)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better caching
COPY requirements-app.txt .
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-app.txt

# Copy application code and dependencies
COPY app.py .
COPY langgraph_app.py .
COPY lib/ ./lib/
COPY images/ ./images/

# Copy configuration files
COPY .streamlit/ ./.streamlit/

# Create necessary directories with proper permissions
RUN mkdir -p /app/uploads /app/output /app/temp /app/logs && \
    chmod 755 /app/uploads /app/output /app/temp /app/logs

# Create a non-root user for security (works on all platforms)
RUN useradd -m -u 1000 -s /bin/bash shusrusha && \
    chown -R shusrusha:shusrusha /app
USER shusrusha

# Expose the Streamlit port
EXPOSE 8501

# Health check (works on Windows and macOS Docker)
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Default command with error handling
CMD ["streamlit", "run", "app.py", \
     "--server.address", "0.0.0.0", \
     "--server.port", "8501", \
     "--server.headless", "true", \
     "--server.enableCORS", "false", \
     "--server.enableXsrfProtection", "false"]
