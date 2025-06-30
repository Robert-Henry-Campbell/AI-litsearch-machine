# Use slim base with Python 3.12
FROM python:3.12-slim

# Install OS-level dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy your project files
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip \
 && pip install -r requirements.txt

# Default entrypoint (can be overridden at runtime)
#CMD ["python", "run_pipeline.py"]
