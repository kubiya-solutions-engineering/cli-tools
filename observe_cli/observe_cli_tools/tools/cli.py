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
        """List datasets with basic curl."""
        return ObserveCLITool(
            name="observe_list_datasets",
            description="List datasets in the Observe instance with basic curl",
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
            
            # Install required packages if not available
            if ! command -v jq >/dev/null 2>&1 || ! command -v curl >/dev/null 2>&1; then
                echo "Installing required packages..."
                apk add --no-cache jq curl
            fi
            
            # Build URL
            URL="https://$OBSERVE_CUSTOMER_ID.eu-1.observeinc.com/v1/dataset"
            
            echo "Making request to: $URL"
            echo ""
            
            # Make API call and get raw response
            RESPONSE=$(curl -s "$URL" \
                --header "Authorization: Bearer $OBSERVE_CUSTOMER_ID $OBSERVE_API_KEY" \
                --header "Content-Type: application/json")
            
            echo "Raw response:"
            echo "$RESPONSE" | head -20
            echo ""
            
            # If response is valid JSON, show formatted version
            if echo "$RESPONSE" | jq empty 2>/dev/null; then
                echo "Formatted JSON:"
                echo "$RESPONSE" | jq '.'
            else
                echo "Response is not valid JSON"
            fi
            """,
            args=[],
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
            
            if [ -z "$opal_query" ]; then
                echo "Error: opal_query parameter is required"
                exit 1
            fi
            
            # Install required packages if not available
            if ! command -v jq >/dev/null 2>&1 || ! command -v curl >/dev/null 2>&1; then
                echo "Installing required packages..."
                apk add --no-cache jq curl
            fi
            
            # Build query payload
            QUERY_PAYLOAD='{"query": {"stages": [{"input": [{"datasetId": "'$dataset_id'"}], "stageID": "main", "pipeline": "'$opal_query'"}]}}'
            
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
            
            # Echo the curl command for debugging
            echo "Executing curl command:"
            echo "curl -s \"$URL\" \\"
            echo "  --request POST \\"
            echo "  --header \"Authorization: Bearer $OBSERVE_CUSTOMER_ID $OBSERVE_API_KEY\" \\"
            echo "  --header \"Content-Type: application/json\" \\"
            echo "  --data \"$QUERY_PAYLOAD\""
            echo ""
            
            # Execute query
            curl -s "$URL" \
                --request POST \
                --header "Authorization: Bearer $OBSERVE_CUSTOMER_ID $OBSERVE_API_KEY" \
                --header "Content-Type: application/json" \
                --data "$QUERY_PAYLOAD" | jq '.' 2>/dev/null || echo "Error: Failed to parse response"
            """,
            args=[
                Arg(name="dataset_id", description="Dataset ID to query", required=True),
                Arg(name="opal_query", description="OPAL query string (e.g., 'filter severity == \"error\"')", required=True),
                Arg(name="start_time", description="Start time in ISO8601 format (e.g., 2023-04-20T16:20:00Z)", required=False),
                Arg(name="end_time", description="End time in ISO8601 format (e.g., 2023-04-20T16:30:00Z)", required=False),
                Arg(name="interval", description="Time interval (e.g., 1h, 10m, 30s)", required=False)
            ],
            image="alpine:latest"
        )

CLITools()