# Use official lightweight Python base
FROM python:3.11-slim

# Prevent Python from writing .pyc files & enable unbuffered stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies, headless LibreOffice, and font libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    fonts-dejavu \
    fonts-liberation \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set up an unprivileged system user for sandboxed security
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source files
COPY converter_core.py .
COPY security.py .
COPY main.py .

# Create temp storage directory and grant ownership to non-root appuser
RUN mkdir -p /tmp/universal_converter_jobs && \
    chown -R appuser:appuser /app /tmp/universal_converter_jobs

# Switch away from root user
USER appuser

# Expose FastAPI port
EXPOSE 8000

# Launch Uvicorn with standard production settings
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]