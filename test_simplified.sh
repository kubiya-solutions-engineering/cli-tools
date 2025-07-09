#!/bin/bash

# Test the simplified jq command
echo "Testing simplified jq command..."

# Simulate the variables
FULL_DATASET_ID="o::115742482447:dataset:41041574"
opal_query='filter severity == \"error\"'

echo "Dataset ID: $FULL_DATASET_ID"
echo "Query: $opal_query"

# Test the simplified jq command
QUERY_PAYLOAD=$(jq -n --arg datasetId "$FULL_DATASET_ID" --arg pipeline "$opal_query" '{"query":{"stages":[{"input":[{"datasetId":$datasetId,"name":"main"}],"stageID":"main","pipeline":$pipeline}]}}')

echo "Query payload:"
echo "$QUERY_PAYLOAD" | jq '.'

echo "Test completed successfully!" 