# Use the official Python image as a base
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install necessary packages
RUN apt-get update && apt-get install -y \
    firefox-esr \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code into the container
COPY src/ .

# Copy geckodriver
COPY geckodriver.exe /usr/local/bin/geckodriver
RUN chmod +x /usr/local/bin/geckodriver

# Create directories for downloads and comprobantes
RUN mkdir -p /app/comprobantes /app/descargas

# Set the entry point for the container
CMD ["python", "main.py"]