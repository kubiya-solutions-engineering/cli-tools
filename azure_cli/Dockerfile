FROM mcr.microsoft.com/azure-cli:latest

# Install additional required packages
RUN apk add --no-cache \
    python3 \
    py3-pip \
    jq \
    bash \
    git

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --break-system-packages -r requirements.txt

# Copy the package
COPY . .

# Install the package
RUN pip3 install --break-system-packages -e . 