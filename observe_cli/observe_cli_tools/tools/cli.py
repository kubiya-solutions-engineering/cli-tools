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
        """Execute OPAL queries on datasets with smart dataset selection and JQ-based query building."""
        return ObserveCLITool(
            name="observe_opal_query",
            description="Execute OPAL queries on Observe datasets. Use JQ to build complex queries safely. Examples: jq -n '{query: {stages: [{input: [{inputName: \"main\", datasetId: \"41231950\"}], stageID: \"main\", pipeline: \"filter message ~ error | limit 10\"}]}}' | observe_opal_query dataset_id=41231950 query_json=@- OR simple usage: observe_opal_query dataset_id=kong opal_query='filter message ~ error'",
            content="""#!/bin/sh
    set -e

    # Environment validation
    if [ -z "$OBSERVE_API_KEY" ] || [ -z "$OBSERVE_CUSTOMER_ID" ]; then
        echo "Error: OBSERVE_API_KEY and OBSERVE_CUSTOMER_ID environment variables are required"
        exit 1
    fi

    # Install required packages
    if ! command -v jq >/dev/null 2>&1 || ! command -v curl >/dev/null 2>&1; then
        apk add --no-cache jq curl >/dev/null 2>&1 || {
            echo "Error: Failed to install required packages (jq, curl)"
            exit 1
        }
    fi

    # Parse arguments with defaults
    DATASET_ID="${dataset_id:-}"
    OPAL_QUERY="${opal_query:-}"
    QUERY_JSON="${query_json:-}"
    INTERVAL="${interval:-}"

    if [ -z "$DATASET_ID" ]; then
        echo "Error: dataset_id is required"
        echo "Usage: dataset_id='<id_or_name>' [opal_query='<query>' | query_json='<json>'] [interval='<time>']"
        exit 1
    fi

    echo "=== Observe OPAL Query Tool ==="
    echo "Dataset: $DATASET_ID"
    if [ -n "$INTERVAL" ]; then
        echo "Interval: $INTERVAL"
    fi
    echo ""

    # Resolve dataset ID
    FULL_DATASET_ID=""
    if echo "$DATASET_ID" | grep -q "^[0-9][0-9]*$"; then
        # Numeric ID - convert to full format
        FULL_DATASET_ID="o::$OBSERVE_CUSTOMER_ID:dataset:$DATASET_ID"
        echo "✓ Using numeric dataset ID: $DATASET_ID"
    elif echo "$DATASET_ID" | grep -q "^o::.*:dataset:.*"; then
        # Already full format
        FULL_DATASET_ID="$DATASET_ID"
        echo "✓ Using full dataset ID: $DATASET_ID"
    else
        # Search by name
        echo "🔍 Searching for dataset: $DATASET_ID"
        
        DATASET_URL="https://$OBSERVE_CUSTOMER_ID.eu-1.observeinc.com/v1/dataset"
        DATASET_RESPONSE=$(curl -s "$DATASET_URL" \
            --header "Authorization: Bearer $OBSERVE_CUSTOMER_ID $OBSERVE_API_KEY" \
            --header "Content-Type: application/json")
        
        if ! echo "$DATASET_RESPONSE" | jq empty 2>/dev/null; then
            echo "❌ Error: Invalid response from dataset API"
            exit 1
        fi
        
        # Find matching datasets - search in both data and root level
        DATASETS=$(echo "$DATASET_RESPONSE" | jq -r '.data // . // []')
        
        if [ "$DATASETS" = "[]" ]; then
            echo "❌ No datasets found in response"
            exit 1
        fi
        
        # Search case-insensitively
        MATCHES=$(echo "$DATASETS" | jq -r --arg search "$DATASET_ID" '
            map(select(.config.name | ascii_downcase | contains($search | ascii_downcase))) 
            | map({id: .meta.id, name: .config.name, type: .state.kind})
        ')
        
        MATCH_COUNT=$(echo "$MATCHES" | jq length)
        
        if [ "$MATCH_COUNT" -eq 0 ]; then
            echo "❌ No datasets found matching '$DATASET_ID'"
            echo ""
            echo "Available datasets (first 10):"
            echo "$DATASETS" | jq -r '.[] | select(.meta.id != null) | "\(.meta.id | split(":")[3]) - \(.config.name)"' | head -10
            exit 1
        elif [ "$MATCH_COUNT" -gt 1 ]; then
            echo "❌ Found $MATCH_COUNT datasets matching '$DATASET_ID'. Please be more specific:"
            echo "$MATCHES" | jq -r '.[] | "  \(.id | split(":")[3]) - \(.name) (\(.type))"'
            exit 1
        else
            FULL_DATASET_ID=$(echo "$MATCHES" | jq -r '.[0].id')
            DATASET_NAME=$(echo "$MATCHES" | jq -r '.[0].name')
            DATASET_TYPE=$(echo "$MATCHES" | jq -r '.[0].type')
            echo "✓ Found dataset: $DATASET_NAME ($DATASET_TYPE)"
            echo "  ID: $FULL_DATASET_ID"
        fi
    fi

    echo ""

    # Build query JSON
    QUERY_BODY=""
    if [ -n "$QUERY_JSON" ]; then
        # Use provided JSON query
        echo "📝 Using provided JSON query"
        if [ "$QUERY_JSON" = "@-" ]; then
            QUERY_BODY=$(cat)
        else
            QUERY_BODY="$QUERY_JSON"
        fi
        
        # Validate JSON
        if ! echo "$QUERY_BODY" | jq empty 2>/dev/null; then
            echo "❌ Error: Invalid JSON in query_json"
            exit 1
        fi
    elif [ -n "$OPAL_QUERY" ]; then
        # Build JSON from OPAL query string
        echo "📝 Building query from OPAL string: $OPAL_QUERY"
        
        QUERY_BODY=$(jq -n \
            --arg datasetId "$FULL_DATASET_ID" \
            --arg pipeline "$OPAL_QUERY" \
            '{
                query: {
                    stages: [{
                        input: [{
                            inputName: "main",
                            datasetId: $datasetId
                        }],
                        stageID: "main",
                        pipeline: $pipeline
                    }]
                }
            }')
    else
        echo "❌ Error: Either opal_query or query_json is required"
        echo ""
        echo "Examples:"
        echo "  # Simple OPAL query:"
        echo "  opal_query='filter message ~ error | limit 10'"
        echo ""
        echo "  # Complex JQ-built query:"
        echo "  query_json='\$(jq -n --arg id \"$FULL_DATASET_ID\" '"'"'{query: {stages: [{input: [{inputName: \"main\", datasetId: \$id}], stageID: \"main\", pipeline: \"filter severity == \\\"error\\\" | limit 5\"}]}}'"'"')'"
        exit 1
    fi

    # Show query payload
    echo "Query payload:"
    echo "$QUERY_BODY" | jq '.'
    echo ""

    # Build API URL
    API_URL="https://$OBSERVE_CUSTOMER_ID.eu-1.observeinc.com/v1/meta/export/query"
    if [ -n "$INTERVAL" ]; then
        API_URL="$API_URL?interval=$INTERVAL"
    fi

    echo "🚀 Executing query..."
    echo "URL: $API_URL"
    echo ""

    # Execute query
    RESPONSE=$(curl -s "$API_URL" \
        --request POST \
        --header "Authorization: Bearer $OBSERVE_CUSTOMER_ID $OBSERVE_API_KEY" \
        --header "Content-Type: application/json" \
        --header "Accept: application/x-ndjson" \
        --data "$QUERY_BODY")

    # Check if we got a response
    if [ -z "$RESPONSE" ]; then
        echo "❌ Error: No response from API"
        exit 1
    fi

    # Process response
    if echo "$RESPONSE" | jq empty 2>/dev/null; then
        echo "📊 Query Results:"
        echo "$RESPONSE" | jq '.'
        
        # Check for errors in response
        ERROR_MSG=$(echo "$RESPONSE" | jq -r '.error // .message // empty')
        if [ -n "$ERROR_MSG" ]; then
            echo ""
            echo "⚠️  Query completed with messages/errors:"
            echo "$ERROR_MSG"
            
            # Provide helpful guidance for common OPAL issues
            if echo "$ERROR_MSG" | grep -q "expected one of"; then
                echo ""
                echo "💡 OPAL Syntax Help:"
                echo "  • Use pattern matching: filter message ~ error"
                echo "  • Quote string values: filter severity == \"error\""
                echo "  • Common operators: ==, !=, ~, !~, <, >"
                echo "  • Pipe operations: filter ... | limit 10 | pick_col timestamp, message"
                echo ""
                echo "  Example JQ query builder:"
                echo "  jq -n --arg id \"$FULL_DATASET_ID\" \\"
                echo "    '{query: {stages: [{input: [{inputName: \"main\", datasetId: \$id}], stageID: \"main\", pipeline: \"filter message ~ error | limit 5\"}]}}'"
            fi
        fi
    else
        echo "📄 Raw Response (possibly NDJSON):"
        echo "$RESPONSE"
    fi
    """,
            args=[
                Arg(name="dataset_id", description="Dataset identifier: numeric ID (e.g., '41231950'), full ID (e.g., 'o::123:dataset:456'), or dataset name (e.g., 'kong', 'nginx'). Names are searched case-insensitively.", required=True),
                Arg(name="opal_query", description="OPAL query string. Use simple syntax like 'filter message ~ error | limit 10'. For complex queries, consider using query_json with JQ instead.", required=False),
                Arg(name="query_json", description="Complete JSON query body. Use JQ to build complex queries safely: jq -n --arg id 'DATASET_ID' '{query: {stages: [{input: [{inputName: \"main\", datasetId: $id}], stageID: \"main\", pipeline: \"YOUR_OPAL_QUERY\"}]}}'. Use '@-' to read from stdin.", required=False),
                Arg(name="interval", description="Time interval for the query (e.g., '1h', '30m', '10s'). Required for Event datasets when no explicit time bounds are provided.", required=False)
            ],
            image="alpine:latest"
        )

CLITools()