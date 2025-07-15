# Data-to-S3 Tools

A collection of Kubiya tools for processing CSV data with custom deduplication rules and uploading to S3.

## Features

- CSV Data Processing with intelligent parsing
- Custom Deduplication rules based on source and rights profiles
- S3 Upload functionality
- Flexible input (file or direct content)
- Fallback processing for maximum compatibility
- Comprehensive data quality reports

## Tool: process_csv_to_s3

Process CSV data with custom deduplication rules and upload to S3.

**Arguments:**
- `data_source` (optional): Path to the CSV file to process
- `data_content` (optional): Direct CSV content as string
- `output_location` (required): S3 path where processed data should be stored
- `s3_bucket` (required): S3 bucket name for upload
- `s3_key` (required): S3 key/path for the processed file

**Required Environment Variables:**
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_REGION`: AWS region (optional)

## Installation

```bash
pip install -r requirements.txt
```

## Docker Build

```bash
docker build -t data-to-s3-tools .
```
