# Base image
FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Dependencies stage
FROM base AS deps
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Runner stage
FROM base AS runner
WORKDIR /app

# Create non-root user
RUN groupadd --system --gid 1000 django && \
    useradd --system --uid 1000 --gid django django

# Copy dependencies from deps stage
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=django:django Ashpazbashi/ ./Ashpazbashi/
COPY --chown=django:django requirements.txt ./requirements.txt

WORKDIR /app/Ashpazbashi

# Collect static files (will be run during container startup if needed)
# RUN python manage.py collectstatic --noinput

USER django

EXPOSE 8000

# Use gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "Ashpazbashi.wsgi:application"]

