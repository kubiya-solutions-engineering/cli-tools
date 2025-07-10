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
        return ObserveCLITool(
            name="observe_opal_query",
            description=(
                "Execute OPAL queries on Observe datasets. Supports raw OPAL string or prebuilt query JSON via stdin. "
                "Use `opal_query='filter message ~ \"error\" | limit 10'` for simple searches, "
                "or `query_json=@-` for full JSON query piped via stdin."
            ),
            content="""
            #!/bin/sh
            set -e

            # Validate environment
            if [ -z "$OBSERVE_API_KEY" ] || [ -z "$OBSERVE_CUSTOMER_ID" ]; then
                echo "❌ OBSERVE_API_KEY and OBSERVE_CUSTOMER_ID are required"
                exit 1
            fi

            apk add --no-cache jq curl >/dev/null 2>&1 || {
                echo "❌ Failed to install required tools"
                exit 1
            }

            dataset_id="$dataset_id"
            opal_query="$opal_query"
            query_json="$query_json"
            interval="$interval"

            if [ -z "$dataset_id" ]; then
                echo "❌ dataset_id is required"
                exit 1
            fi

            echo "🔍 Resolving dataset: $dataset_id"

            if echo "$dataset_id" | grep -qE '^[0-9]+$'; then
                FULL_DATASET_ID="o::$OBSERVE_CUSTOMER_ID:dataset:$dataset_id"
            elif echo "$dataset_id" | grep -qE '^o::.*:dataset:.*$'; then
                FULL_DATASET_ID="$dataset_id"
            else
                API_URL="https://$OBSERVE_CUSTOMER_ID.eu-1.observeinc.com/v1/dataset"
                RESPONSE=$(curl -s "$API_URL" \
                    --header "Authorization: Bearer $OBSERVE_CUSTOMER_ID $OBSERVE_API_KEY" \
                    --header "Content-Type: application/json")

                MATCHES=$(echo "$RESPONSE" | jq -r --arg search "$dataset_id" '
                    (.data // .) | map(select(.config.name | ascii_downcase | contains($search | ascii_downcase)))')

                COUNT=$(echo "$MATCHES" | jq length)
                if [ "$COUNT" -eq 0 ]; then
                    echo "❌ No datasets matched '$dataset_id'"
                    exit 1
                elif [ "$COUNT" -gt 1 ]; then
                    echo "❌ Multiple matches found. Please be more specific:"
                    echo "$MATCHES" | jq -r '.[] | "  \(.meta.id | split(":")[3]) - \(.config.name) (\(.state.kind))"'
                    exit 1
                else
                    FULL_DATASET_ID=$(echo "$MATCHES" | jq -r '.[0].meta.id')
                    echo "✓ Found: $FULL_DATASET_ID"
                fi
            fi

            # Construct query
            if [ -n "$query_json" ]; then
                if [ "$query_json" = "@-" ]; then
                    QUERY_BODY=$(cat)
                else
                    QUERY_BODY="$query_json"
                fi

                if ! echo "$QUERY_BODY" | jq empty 2>/dev/null; then
                    echo "❌ Provided query_json is not valid JSON"
                    exit 1
                fi
            elif [ -n "$opal_query" ]; then
                echo "🛠 Building query JSON from OPAL: $opal_query"
                QUERY_BODY=$(jq -n --arg datasetId "$FULL_DATASET_ID" --arg pipeline "$opal_query" '
                {
                    query: {
                        stages: [
                            {
                                input: [{ inputName: "main", datasetId: $datasetId }],
                                stageID: "main",
                                pipeline: $pipeline
                            }
                        ]
                    }
                }')
            else
                echo "❌ Either opal_query or query_json must be provided"
                exit 1
            fi

            echo "📦 Final query JSON:"
            echo "$QUERY_BODY" | jq .

            QUERY_URL="https://$OBSERVE_CUSTOMER_ID.eu-1.observeinc.com/v1/meta/export/query"
            if [ -n "$interval" ]; then
                QUERY_URL="$QUERY_URL?interval=$interval"
            fi

            echo "🚀 Executing OPAL query..."
            RESPONSE=$(curl -s "$QUERY_URL" \
                --request POST \
                --header "Authorization: Bearer $OBSERVE_CUSTOMER_ID $OBSERVE_API_KEY" \
                --header "Content-Type: application/json" \
                --header "Accept: application/x-ndjson" \
                --data "$QUERY_BODY")

            echo ""
            if echo "$RESPONSE" | jq empty >/dev/null 2>&1; then
                echo "📊 Query Result:"
                echo "$RESPONSE" | jq .
            else
                echo "📄 Non-JSON response:"
                echo "$RESPONSE"
            fi
            """,
            args=[
                Arg(name="dataset_id", description="Dataset ID, name, or full dataset URI", required=True),
                Arg(name="opal_query", description="OPAL query string (e.g., 'filter message ~ \"error\"')", required=False),
                Arg(name="query_json", description="Full query JSON body. Use '@-' to read from stdin", required=False),
                Arg(name="interval", description="Optional interval (e.g., '1h', '10m') for event queries", required=False),
            ],
            image="alpine:latest"
        )


CLITools()