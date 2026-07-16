# Use official Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# git is required by Phase 3 (blobless clones + PyDriller history traversal).
# The slim base image does not include it.
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code and runner scripts
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY run.py ./run.py
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

# output/ is written at runtime; attach a Railway Volume at /app/output to persist results
RUN mkdir -p /app/output

# Deploying does NOT auto-run a job. The entrypoint idles until RUN_JOB is set
# (mine | phase2 | phase2-stage-a). See entrypoint.sh and README.
CMD ["bash", "entrypoint.sh"]
