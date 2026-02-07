# Use a small official Python image
FROM python:3.11-slim

# Make Python output show up immediately
ENV PYTHONUNBUFFERED=1

# Create and move into /app inside the container
WORKDIR /app

# Copy ALL your project files into the container
COPY . /app

# Install all Python dependencies your app uses
RUN pip install --no-cache-dir \
    flask \
    flask-cors \
    flask-sqlalchemy \
    sqlalchemy \
    flask-migrate \
    Flask-APScheduler \
    apscheduler \
    python-dotenv \
	pyyaml \ 
    requests

# Your Flask app listens on port 5000
EXPOSE 5000

# Start your app
CMD ["python", "Family_Hub1_0.py"]
