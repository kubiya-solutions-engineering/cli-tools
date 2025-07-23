FROM python:3.11-slim

# Install additional required packages
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    bash \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the package
COPY . .

# Install the package
RUN pip install --no-cache-dir -e . 