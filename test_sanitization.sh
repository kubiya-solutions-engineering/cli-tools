#!/bin/bash

# Test the input sanitization
dataset_id="kong"
opal_query='filter severity == "error"'
interval="1h"

echo "Testing input sanitization with AI-style input..."

# Simulate the dataset search
echo "Searching for dataset: $dataset_id"
echo "Found dataset: Kong/Kong Server Logs - Production (Event)"
echo "Dataset ID: o::115742482447:dataset:41041574"

# Test the sanitization logic
echo "Original query: $opal_query"

# Test with the problematic input that the AI sends
PROBLEMATIC_QUERY='filter severity == "error"'
echo "Problematic query (AI input): $PROBLEMATIC_QUERY"

# Sanitize the opal_query to handle JSON input with unescaped quotes
# Handle the case where the AI passes the query with unescaped quotes
# First, check if the query starts and ends with quotes (JSON string format)
if [[ "$PROBLEMATIC_QUERY" =~ ^\".*\"$ ]]; then
    # Remove outer quotes and unescape inner quotes
    SANITIZED_QUERY=$(echo "$PROBLEMATIC_QUERY" | sed 's/^"//;s/"$//' | sed 's/\\"/"/g')
else
    # Query is already in the correct format
    SANITIZED_QUERY="$PROBLEMATIC_QUERY"
fi

# Use the sanitized query
opal_query="$SANITIZED_QUERY"

echo "Sanitized query: $opal_query"

# Test the query payload construction
FULL_DATASET_ID="o::115742482447:dataset:41041574"

# Build query payload using jq for proper JSON handling
QUERY_PAYLOAD=$(jq -n \
    --arg datasetId "$FULL_DATASET_ID" \
    --arg pipeline "$opal_query" \
    '{
        "query": {
            "stages": [
                {
                    "input": [
                        {
                            "datasetId": $datasetId,
                            "name": "main"
                        }
                    ],
                    "stageID": "main",
                    "pipeline": $pipeline
                }
            ]
        }
    }')

echo "Query payload:"
echo "$QUERY_PAYLOAD" | jq '.'

echo "Test completed successfully!" 