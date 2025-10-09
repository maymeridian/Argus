FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    poppler-utils \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install olmOCR with GPU support
RUN pip install --no-cache-dir olmocr[gpu] vllm

# Set working directory
WORKDIR /app

# Copy application files
COPY main.py .
COPY reader.py .
COPY matcher.py .
COPY renamer.py .

# Run the main script
CMD ["python", "main.py"]
