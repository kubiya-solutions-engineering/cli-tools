FROM alpine:latest

# Install required packages including Azure CLI
RUN apk add --no-cache \
    python3 \
    py3-pip \
    jq \
    curl \
    bash \
    git

# Install Azure CLI
RUN curl -L https://aka.ms/InstallAzureCli | bash

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy the package
COPY . .

# Install the package
RUN pip3 install -e . 