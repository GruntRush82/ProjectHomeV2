# Use a small official Python image
FROM python:3.12-slim

# Make Python output show up immediately
ENV PYTHONUNBUFFERED=1

# Create and move into /app inside the container
WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app

# Your Flask app listens on port 5000
EXPOSE 5000

# Start via the new entry point
CMD ["python", "run.py"]
