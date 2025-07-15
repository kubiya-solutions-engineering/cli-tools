FROM python:3.11-slim

# Install required packages
RUN pip install --no-cache-dir \
    kubiya-sdk>=0.1.0 \
    requests>=2.31.0 \
    pyyaml>=6.0.1 \
    pandas>=1.5.0 \
    boto3>=1.26.0

# Copy the tool code
COPY data_to_s3_tools/ /app/data_to_s3_tools/
COPY setup.py /app/
COPY requirements.txt /app/

# Install the package
WORKDIR /app
RUN pip install -e .

# Set the entrypoint
CMD ["python", "-c", "from data_to_s3_tools import DataProcessorTools; DataProcessorTools()"] 