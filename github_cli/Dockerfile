FROM alpine:latest

# Install required packages including GitHub CLI
RUN apk add --no-cache \
    python3 \
    py3-pip \
    jq \
    curl \
    github-cli \
    git

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy the package
COPY . .

# Install the package
RUN pip3 install -e . 