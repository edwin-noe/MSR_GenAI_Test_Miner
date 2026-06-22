# Use official Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY src/ ./src/

# output/ is written at runtime; attach a Railway Volume at /app/output to persist results
RUN mkdir -p /app/output

# Run the app
CMD ["python", "-m", "src.main"]
