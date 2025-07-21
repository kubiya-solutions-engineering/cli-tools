FROM alpine:latest

# Install required packages including Azure CLI and Bicep CLI
RUN apk add --no-cache \
    python3 \
    py3-pip \
    jq \
    curl \
    bash \
    git

# Install Azure CLI
RUN apk add --no-cache azure-cli

# Install Bicep CLI
RUN curl -Lo bicep https://github.com/Azure/bicep/releases/latest/download/bicep-linux-x64 && \
    chmod +x ./bicep && \
    mv ./bicep /usr/local/bin/bicep

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy the package
COPY . .

# Install the package
RUN pip3 install -e . 