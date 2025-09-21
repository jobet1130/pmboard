# Use official Python 3.12 image as base
FROM python:3.12-slim-bookworm as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PYTHONFAULTHANDLER=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# First copy only the dependency files for better caching
COPY pyproject.toml README.md ./

# Install build dependencies
RUN pip install --upgrade pip && \
    pip install setuptools wheel

# Copy the entire project first
COPY . .

# Now install the package in development mode
RUN pip install -e .

# Production stage
FROM base as production

# Copy from base stage
COPY --from=base /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=base /app /app

# Install production dependencies
RUN pip install gunicorn

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]

# Development stage
FROM base as development

# Install development dependencies
RUN pip install -e ".[dev]"

# Set default command to run the development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Expose the port the app runs on
EXPOSE 8000

# Command to run the development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Celery worker stage
FROM base as celery-worker

# Install production dependencies
RUN pip install -e ".[dev]"

# Create directory for celery scripts
RUN mkdir -p /app/docker/celery/worker

# Create a simple start script for Celery worker
RUN echo '#!/bin/sh\n\
celery -A pmboard worker -l INFO\n' > /start-celeryworker.sh && \
    chmod +x /start-celeryworker.sh

# Command to run celery worker
CMD ["/start-celeryworker.sh"]

# Celery beat stage
FROM base as celery-beat

# Install production dependencies
RUN pip install -e ".[dev]"

# Create directory for celery beat scripts
RUN mkdir -p /app/docker/celery/beat

# Create a simple start script for Celery beat
RUN echo '#!/bin/sh\n\
celery -A pmboard beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler\n' > /start-celerybeat.sh && \
    chmod +x /start-celerybeat.sh

# Command to run celery beat
CMD ["/start-celerybeat.sh"]