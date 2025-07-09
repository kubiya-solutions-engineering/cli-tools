from typing import List
import sys
from .base import ObserveCLITool, Arg
from kubiya_sdk.tools.registry import tool_registry

class CLITools:
    """Simplified Observe API tools for dataset listing and OPAL queries."""

    def __init__(self):
        """Initialize and register Observe API tools."""
        try:
            tools = [
                self.list_datasets(),
                self.execute_opal_query()
            ]
            
            for tool in tools:
                try:
                    tool_registry.register("observe_cli", tool)
                    print(f"✅ Registered: {tool.name}")
                except Exception as e:
                    print(f"❌ Failed to register {tool.name}: {str(e)}", file=sys.stderr)
                    raise
        except Exception as e:
            print(f"❌ Failed to register Observe API wrapper tools: {str(e)}", file=sys.stderr)
            raise

    def list_datasets(self) -> ObserveCLITool:
        """List all datasets with clean output."""
        return ObserveCLITool(
            name="observe_list_datasets",
            description="List all datasets in the Observe instance with clean output",
            content="""
            # Check required environment variables
            if [ -z "$OBSERVE_API_KEY" ]; then
                echo "Error: OBSERVE_API_KEY environment variable is required"
                exit 1
            fi
            
            if [ -z "$OBSERVE_CUSTOMER_ID" ]; then
                echo "Error: OBSERVE_CUSTOMER_ID environment variable is required"
                exit 1
            fi
            
            # Install required packages silently if not available
            if ! command -v jq >/dev/null 2>&1 || ! command -v curl >/dev/null 2>&1; then
                apk add --no-cache jq curl >/dev/null 2>&1
            fi
            
            # Build URL
            URL="https://$OBSERVE_CUSTOMER_ID.eu-1.observeinc.com/v1/dataset"
            
            # Make API call and get response
            RESPONSE=$(curl -s "$URL" \
                --header "Authorization: Bearer $OBSERVE_CUSTOMER_ID $OBSERVE_API_KEY" \
                --header "Content-Type: application/json")
            
            # Check if response is valid JSON
            if ! echo "$RESPONSE" | jq empty 2>/dev/null; then
                echo "Error: Invalid JSON response from API"
                exit 1
            fi
            
            # Extract datasets array
            DATASETS=$(echo "$RESPONSE" | jq -r '.data // . // []')
            
            # Get total count
            TOTAL_COUNT=$(echo "$DATASETS" | jq length)
            
            # Show summary if requested
            if [ "$show_summary" = "true" ]; then
                echo "=== Dataset Summary ==="
                echo "Total datasets: $TOTAL_COUNT"
                echo "========================"
                echo ""
            fi
            
            # Show all datasets in clean format
            echo "$DATASETS" | jq -r '.[] | "\(.meta.id) - \(.config.name) (\(.state.kind))"'
            """,
            args=[
                Arg(name="show_summary", description="Show summary info (default: false)", required=False)
            ],
            image="alpine:latest"
        )

    def execute_opal_query(self) -> ObserveCLITool:
        """Execute OPAL queries on datasets with smart dataset selection."""
        return ObserveCLITool(
            name="observe_opal_query",
            description="Execute OPAL queries on Observe datasets. Can search by dataset name or use dataset ID directly.",
            content="""
            # Check required environment variables
            if [ -z "$OBSERVE_API_KEY" ]; then
                echo "Error: OBSERVE_API_KEY environment variable is required"
                exit 1
            fi
            
            if [ -z "$OBSERVE_CUSTOMER_ID" ]; then
                echo "Error: OBSERVE_CUSTOMER_ID environment variable is required"
                exit 1
            fi
            
            if [ -z "$dataset_id" ]; then
                echo "Error: dataset_id parameter is required"
                exit 1
            fi
            
            # Install required packages silently if not available
            if ! command -v jq >/dev/null 2>&1 || ! command -v curl >/dev/null 2>&1; then
                apk add --no-cache jq curl >/dev/null 2>&1
            fi
            
            # Determine if dataset_id is a numeric ID, full ID, or a name search
            if [[ "$dataset_id" =~ ^[0-9]+$ ]]; then
                # Numeric ID - convert to full ID
                FULL_DATASET_ID="o::$OBSERVE_CUSTOMER_ID:dataset:$dataset_id"
                echo "Converting numeric ID $dataset_id to full ID: $FULL_DATASET_ID"
            elif [[ "$dataset_id" =~ ^o::.*:dataset:.* ]]; then
                # Full dataset ID - use as is
                FULL_DATASET_ID="$dataset_id"
            else
                # Treat as dataset name search
                echo "Searching for dataset: $dataset_id"
                
                # Get all datasets
                DATASET_URL="https://$OBSERVE_CUSTOMER_ID.eu-1.observeinc.com/v1/dataset"
                DATASET_RESPONSE=$(curl -s "$DATASET_URL" \
                    --header "Authorization: Bearer $OBSERVE_CUSTOMER_ID $OBSERVE_API_KEY" \
                    --header "Content-Type: application/json")
                
                # Check if response is valid JSON
                if ! echo "$DATASET_RESPONSE" | jq empty 2>/dev/null; then
                    echo "Error: Invalid JSON response from dataset API"
                    exit 1
                fi
                
                # Extract datasets array
                DATASETS=$(echo "$DATASET_RESPONSE" | jq -r '.data // . // []')
                
                # Search for datasets matching the search term (case insensitive)
                MATCHING_DATASETS=$(echo "$DATASETS" | jq -r --arg search "$dataset_id" '.[] | select(.config.name | ascii_downcase | contains($search | ascii_downcase)) | {id: .meta.id, name: .config.name, type: .state.kind}' | jq -s '.')
                
                # Count matches
                MATCH_COUNT=$(echo "$MATCHING_DATASETS" | jq length)
                
                if [ "$MATCH_COUNT" -eq 0 ]; then
                    echo "No datasets found matching '$dataset_id'"
                    echo ""
                    echo "Available datasets containing similar terms:"
                    echo "$DATASETS" | jq -r '.[] | .config.name' | grep -i "$dataset_id" | head -10 || echo "No similar datasets found"
                    exit 1
                fi
                
                if [ "$MATCH_COUNT" -gt 1 ]; then
                    echo "Found $MATCH_COUNT datasets matching '$dataset_id':"
                    echo "$MATCHING_DATASETS" | jq -r '.[] | "\(.id) - \(.name) (\(.type))"'
                    echo ""
                    echo "Please be more specific with your search term or use the dataset ID directly."
                    exit 1
                fi
                
                # Get the single matching dataset
                FULL_DATASET_ID=$(echo "$MATCHING_DATASETS" | jq -r '.[0].id')
                DATASET_NAME=$(echo "$MATCHING_DATASETS" | jq -r '.[0].name')
                DATASET_TYPE=$(echo "$MATCHING_DATASETS" | jq -r '.[0].type')
                
                echo "Found dataset: $DATASET_NAME ($DATASET_TYPE)"
                echo "Dataset ID: $FULL_DATASET_ID"
            fi
            
            # Set default query if none provided
            if [ -z "$opal_query" ]; then
                opal_query="limit 10"
                echo "No query provided, using default: $opal_query"
            fi
            
            # Build query payload using jq to properly escape JSON
            QUERY_PAYLOAD=$(jq -n \
                --arg datasetId "$FULL_DATASET_ID" \
                --arg pipeline "$opal_query" \
                '{
                    "query": {
                        "stages": [
                            {
                                "input": [{"datasetId": $datasetId}],
                                "stageID": "main",
                                "pipeline": $pipeline
                            }
                        ]
                    }
                }')
            
            # Build query parameters
            QUERY_PARAMS=""
            if [ -n "$start_time" ]; then
                QUERY_PARAMS="${QUERY_PARAMS}startTime=$start_time&"
            fi
            if [ -n "$end_time" ]; then
                QUERY_PARAMS="${QUERY_PARAMS}endTime=$end_time&"
            fi
            if [ -n "$interval" ]; then
                QUERY_PARAMS="${QUERY_PARAMS}interval=$interval&"
            fi
            # Remove trailing &
            QUERY_PARAMS=$(echo "$QUERY_PARAMS" | sed 's/&$//')
            
            # Build URL
            URL="https://$OBSERVE_CUSTOMER_ID.eu-1.observeinc.com/v1/meta/export/query"
            if [ -n "$QUERY_PARAMS" ]; then
                URL="$URL?$QUERY_PARAMS"
            fi
            
            echo "Executing query: $opal_query"
            echo ""
            
            # Execute query
            RESPONSE=$(curl -s "$URL" \
                --request POST \
                --header "Authorization: Bearer $OBSERVE_CUSTOMER_ID $OBSERVE_API_KEY" \
                --header "Content-Type: application/json" \
                --data "$QUERY_PAYLOAD")
            
            # Check if response is valid JSON
            if ! echo "$RESPONSE" | jq empty 2>/dev/null; then
                echo "Error: Invalid JSON response from API"
                echo "Response: $RESPONSE"
                exit 1
            fi
            
            # Show formatted response
            echo "$RESPONSE" | jq '.'
            """,
            args=[
                Arg(name="dataset_id", description="Dataset ID (numeric like 41231950), full ID, or dataset name (e.g., 'kong', 'monitor')", required=True),
                Arg(name="opal_query", description="OPAL query string (default: 'limit 10', examples: 'filter severity == \"error\"', 'limit 5')", required=False),
                Arg(name="start_time", description="Start time in ISO8601 format (e.g., 2023-04-20T16:20:00Z)", required=False),
                Arg(name="end_time", description="End time in ISO8601 format (e.g., 2023-04-20T16:30:00Z)", required=False),
                Arg(name="interval", description="Time interval (e.g., 1h, 10m, 30s)", required=False)
            ],
            image="alpine:latest"
        )

CLITools()