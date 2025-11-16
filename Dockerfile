FROM python:3.11-slim

# Install system dependencies required by WeasyPrint
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy application files
COPY . .

# Create output directory
RUN mkdir -p /app/output

# Make scripts executable
RUN chmod +x server.py 2>/dev/null || true

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port for web interface
EXPOSE 5000

# Default command - run web server
CMD ["python3", "server.py"]
