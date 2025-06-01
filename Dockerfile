# Use official python base image
FROM python:3.12-slim

# Set workdir inside container
WORKDIR /app

# Copy project files to /app
COPY . /app

# Install system dependencies for venv and supervisor
RUN apt-get update && apt-get install -y \
    python3-venv \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtualenv
RUN python3 -m venv venv

# Install python dependencies inside venv
RUN venv/bin/pip install --upgrade pip
RUN venv/bin/pip install -r requirements.txt

# Copy supervisor config
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose ports (adjust as needed)
EXPOSE 5000

# Use supervisor to run multiple processes
CMD ["/usr/bin/supervisord", "-n"]
