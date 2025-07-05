FROM alpine:latest

# Install Python, pip, and curl
RUN apk add --no-cache python3 py3-pip curl

WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

CMD ["python3", "-m", "observe_cli_tools"] 