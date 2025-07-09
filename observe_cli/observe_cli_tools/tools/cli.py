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
            
            # Ensure jq is available
            if ! command -v jq >/dev/null 2>&1; then
                echo "Error: jq is required but not available"
                exit 1
            fi
            
            echo "Using jq for JSON handling and query construction"
            
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
        """Execute OPAL queries on datasets with smart dataset selection (stateless, robust)."""
        return ObserveCLITool(
            name="observe_opal_query",
            description="Execute OPAL queries on Observe datasets. Pass the OPAL query, dataset_id, and interval as positional arguments. Example: 'filter severity == \"error\"' o::115742482447:dataset:41041574 1h. The tool uses jq to build the JSON body and is stateless and robust to quoting issues.",
            content="""
            #!/bin/sh
            set -e
            
            opal_query="$1"
            dataset_id="$2"
            interval="$3"
            
            if [ -z "$opal_query" ] || [ -z "$dataset_id" ]; then
                echo "Usage: $0 <opal_query> <dataset_id> [interval]"
                exit 1
            fi
            
            echo "Query: $opal_query"
            echo "Dataset ID: $dataset_id"
            echo "Interval: $interval"
            
            # Install required packages silently if not available
            if ! command -v jq >/dev/null 2>&1 || ! command -v curl >/dev/null 2>&1; then
                apk add --no-cache jq curl >/dev/null 2>&1
            fi
            
            # Ensure jq is available
            if ! command -v jq >/dev/null 2>&1; then
                echo "Error: jq is required but not available"
                exit 1
            fi
            
            # Build JSON body with jq
            json_body=$(jq -n \
                --arg datasetId "$dataset_id" \
                --arg pipeline "$opal_query" \
                --arg interval "$interval" \
                '{
                    query: {
                        stages: [
                            {
                                input: [{datasetId: $datasetId, name: "main"}],
                                stageID: "main",
                                pipeline: $pipeline
                            }
                        ]
                    },
                    interval: $interval
                }')
            
            # Debug: Show the query payload
            echo "Query payload:"
            echo "$json_body" | jq '.'
            echo ""
            
            # Build URL
            URL="https://$OBSERVE_CUSTOMER_ID.eu-1.observeinc.com/v1/meta/export/query"
            
            # Execute query
            RESPONSE=$(curl -s "$URL" \
                --request POST \
                --header "Authorization: Bearer $OBSERVE_CUSTOMER_ID $OBSERVE_API_KEY" \
                --header "Content-Type: application/json" \
                --header "Accept: application/x-ndjson" \
                --data "$json_body")
            
            # Check if response is valid JSON or NDJSON
            if ! echo "$RESPONSE" | jq empty 2>/dev/null; then
                echo "Raw response (not JSON):"
                echo "$RESPONSE"
            else
                echo "Formatted response:"
                echo "$RESPONSE" | jq '.'
            fi
            """,
            args=[
                Arg(name="opal_query", description="OPAL query string. Example: filter severity == \"error\"", required=True),
                Arg(name="dataset_id", description="Dataset ID (numeric like 41231950), full ID, or dataset name (e.g., 'kong', 'monitor', 'nginx')", required=True),
                Arg(name="interval", description="Time interval (e.g., 1h, 10m, 30s). Required for Event datasets if no start_time/end_time provided", required=False)
            ],
            image="alpine:latest"
        )

CLITools()