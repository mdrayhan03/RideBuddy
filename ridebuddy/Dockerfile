# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install gunicorn psycopg2-binary dj-database-url whitenoise

# Copy project files into the container
COPY . /app/

# Collect static files during build
RUN python manage.py collectstatic --noinput

# Expose port (optional documentation)
EXPOSE 8000

# Default command to run the web server
CMD ["gunicorn", "ridebuddy.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
