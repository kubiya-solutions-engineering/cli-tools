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
        """Execute OPAL queries on datasets."""
        return ObserveCLITool(
            name="observe_opal_query",
            description="Execute OPAL queries on Observe datasets with optional time parameters",
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
            
            # Convert numeric ID to full dataset ID if needed
            if [[ "$dataset_id" =~ ^[0-9]+$ ]]; then
                FULL_DATASET_ID="o::$OBSERVE_CUSTOMER_ID:dataset:$dataset_id"
                echo "Converting numeric ID $dataset_id to full ID: $FULL_DATASET_ID"
            else
                FULL_DATASET_ID="$dataset_id"
            fi
            
            # Set default query if none provided
            if [ -z "$opal_query" ]; then
                opal_query="limit 10"
                echo "No query provided, using default: $opal_query"
            fi
            
            # Build query payload
            QUERY_PAYLOAD='{"query": {"stages": [{"input": [{"datasetId": "'$FULL_DATASET_ID'"}], "stageID": "main", "pipeline": "'$opal_query'"}]}}'
            
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
                Arg(name="dataset_id", description="Dataset ID (numeric like 41231950 or full ID)", required=True),
                Arg(name="opal_query", description="OPAL query string (default: 'limit 10', examples: 'filter severity == \"error\"', 'limit 5')", required=False),
                Arg(name="start_time", description="Start time in ISO8601 format (e.g., 2023-04-20T16:20:00Z)", required=False),
                Arg(name="end_time", description="End time in ISO8601 format (e.g., 2023-04-20T16:30:00Z)", required=False),
                Arg(name="interval", description="Time interval (e.g., 1h, 10m, 30s)", required=False)
            ],
            image="alpine:latest"
        )

CLITools()