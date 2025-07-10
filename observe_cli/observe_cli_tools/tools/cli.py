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
            description="Execute OPAL queries on Observe datasets. The tool accepts named arguments and converts them to positional arguments for the shell script. Example: dataset_id='kong' opal_query='filter message ~ error' interval='1h'. IMPORTANT: For reliable results, use pattern matching (e.g., filter message ~ error) instead of direct field comparison. The tool auto-fixes common syntax issues and provides helpful error guidance. The tool uses jq to build the JSON body and is stateless and robust to quoting issues.",
            content="""
            #!/bin/sh
            set -e
            
            # Accept named arguments from orchestrator and convert to positional
            opal_query="$opal_query"
            dataset_id="$dataset_id"
            interval="$interval"
            
            if [ -z "$opal_query" ] || [ -z "$dataset_id" ]; then
                echo "Error: opal_query and dataset_id are required"
                echo "Usage: opal_query='<query>' dataset_id='<id>' [interval='<time>']"
                exit 1
            fi
            
            # Debug: Show the raw query as received
            echo "Raw query received: '$opal_query'"
            echo "Query: $opal_query"
            echo "Dataset ID: $dataset_id"
            echo "Interval: $interval"
            
            # Strip outer quotes if present (some callers wrap the query string in extra quotes)
            case "$opal_query" in
                \"*\")
                    opal_query=${opal_query#\"}
                    opal_query=${opal_query%\"}
                    ;;
                \'*\')
                    opal_query=${opal_query#\'}
                    opal_query=${opal_query%\'}
                    ;;
            esac
            echo "Sanitized query: $opal_query"
            
            # Preprocess the OPAL query to fix common syntax issues
            # Check for common OPAL syntax issues and provide guidance
            if echo "$opal_query" | grep -q "filter.*==.*[^\"']"; then
                echo "Warning: Query may have unquoted string values"
                echo "Original: $opal_query"
                echo "Consider using: filter severity == \"error\" (with quotes)"
                echo ""
            fi
            
            # Auto-fix common OPAL syntax issues
            # Convert unquoted string values to properly quoted ones
            PROCESSED_QUERY="$opal_query"
            
            # Fix: filter severity == error -> filter severity == "error"
            if echo "$opal_query" | grep -q "filter.*==.*[^\"'][^ ]*$"; then
                PROCESSED_QUERY=$(echo "$opal_query" | sed 's/filter \([^=]*\) == \([^\"'\''][^ ]*\)/filter \1 == "\2"/g')
                if [ "$PROCESSED_QUERY" != "$opal_query" ]; then
                    echo "Auto-fixed query: '$PROCESSED_QUERY'"
                    opal_query="$PROCESSED_QUERY"
                fi
            fi
            
            # Alternative approach: if the query still fails, try pattern matching
            # This is a fallback for when direct field comparison doesn't work
            if echo "$opal_query" | grep -q "filter.*==.*\".*\""; then
                echo "Using direct field comparison query"
            else
                echo "Query format looks good"
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
            
            # Build JSON body with jq - using proper escaping for the OPAL query
            # The key fix: use --arg to properly escape the opal_query variable
            json_body=$(jq -n \
                --arg datasetId "$FULL_DATASET_ID" \
                --arg pipeline "$opal_query" \
                '{
                    query: {
                        stages: [
                            {
                                input: [{inputName: "main", datasetId: $datasetId}],
                                stageID: "main",
                                pipeline: $pipeline
                            }
                        ]
                    }
                }')
            
            # Debug: Show the query payload
            echo "Query payload:"
            echo "$json_body" | jq '.'
            echo ""
            
            # Build URL with query parameters
            URL="https://$OBSERVE_CUSTOMER_ID.eu-1.observeinc.com/v1/meta/export/query"
            if [ -n "$interval" ]; then
                URL="$URL?interval=$interval"
            fi
            
            echo "URL: $URL"
            echo ""
            
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
                
                # Check for OPAL syntax errors and provide helpful guidance
                if echo "$RESPONSE" | jq -r '.message // ""' | grep -q "expected one of"; then
                    echo ""
                    echo "OPAL Syntax Error detected. Common issues:"
                    echo "1. Use double quotes for string values: filter severity == \"error\""
                    echo "2. Use == for equality, not ="
                    echo "3. Check for unescaped quotes in your query"
                    echo ""
                    echo "Try these alternative query patterns:"
                    echo "  # Pattern matching (often more reliable):"
                    echo "  filter message ~ error"
                    echo "  filter log ~ error"
                    echo ""
                    echo "  # Direct field comparison:"
                    echo "  filter severity == \"error\""
                    echo "  filter level == \"error\""
                    echo ""
                    echo "  # Simple queries to test:"
                    echo "  limit 10"
                    echo "  pick_col timestamp, severity"
                    echo ""
                    echo "Debug: The query that was sent:"
                    echo "  $opal_query"
                    echo ""
                    echo "Note: If direct field comparison fails, try pattern matching instead."
                fi
            fi
            """,
            args=[
                Arg(name="opal_query", description="OPAL query string. For reliable results, use pattern matching like 'filter message ~ error' instead of direct field comparison. Examples: 'filter message ~ error', 'filter severity == \"error\"', 'limit 10'", required=True),
                Arg(name="dataset_id", description="Dataset ID (numeric like 41231950), full ID, or dataset name (e.g., 'kong', 'monitor', 'nginx')", required=True),
                Arg(name="interval", description="Time interval (e.g., 1h, 10m, 30s). Required for Event datasets if no start_time/end_time provided", required=False)
            ],
            image="alpine:latest"
        )

CLITools()