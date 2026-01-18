FROM python:3.10-slim

WORKDIR /app

# Install system dependencies including curl for health checks
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download and cache NLP model (for offline deployment)
# This ensures the model is available without internet connectivity
RUN python -m spacy download zh_core_web_sm

# Copy application code
COPY . .

# Create necessary directories for uploads and models
RUN mkdir -p /app/uploads /app/models

# Expose port
EXPOSE 8000

# Health check endpoint - verifies service is responding
# Validates: Requirements 10.7
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application with uvicorn
# Validates: Requirements 10.1, 10.2, 10.3
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
