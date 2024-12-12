# Dockerfile
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libxml2-dev \
    libxslt-dev \
    libz-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt /app/
COPY ./gig_finder /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set the default command to run the Scrapy spider
CMD ["scrapy", "crawl", "freelancer"]