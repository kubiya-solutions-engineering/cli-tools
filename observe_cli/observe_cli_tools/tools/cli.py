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
        """List all datasets with clean output for AI to discover dataset IDs."""
        return ObserveCLITool(
            name="observe_list_datasets",
            description="List all datasets in the Observe instance. Use this to discover dataset IDs and names for building OPAL queries.",
            content="""
            # Validate environment
            if [ -z "$OBSERVE_API_KEY" ] || [ -z "$OBSERVE_CUSTOMER_ID" ]; then
                echo "❌ OBSERVE_API_KEY and OBSERVE_CUSTOMER_ID environment variables are required"
                exit 1
            fi
            
            # Install required packages
            apk add --no-cache jq curl >/dev/null 2>&1 || {
                echo "❌ Failed to install jq and curl"
                exit 1
            }
            
            echo "📋 Fetching datasets from Observe..."
            
            # Get all datasets
            API_URL="https://$OBSERVE_CUSTOMER_ID.eu-1.observeinc.com/v1/dataset"
            RESPONSE=$(curl -s "$API_URL" \
                --header "Authorization: Bearer $OBSERVE_CUSTOMER_ID $OBSERVE_API_KEY" \
                --header "Content-Type: application/json")
            
            # Validate response
            if ! echo "$RESPONSE" | jq empty 2>/dev/null; then
                echo "❌ Invalid JSON response from API"
                echo "Raw response: $RESPONSE"
                exit 1
            fi
            
            # Parse and display datasets
            DATASETS=$(echo "$RESPONSE" | jq -r '.data // . // []')
            TOTAL_COUNT=$(echo "$DATASETS" | jq length)
            
            echo "📊 Found $TOTAL_COUNT datasets"
            echo ""
            
            # Show datasets in a format useful for AI query building
            echo "Available datasets (ID | Name | Type):"
            echo "======================================="
            echo "$DATASETS" | jq -r '.[] | "\(.meta.id | split(":")[3]) | \(.config.name) | \(.state.kind)"' | sort
            
            echo ""
            echo "💡 To use in OPAL queries, use full dataset ID format:"
            echo "   o::$OBSERVE_CUSTOMER_ID:dataset:DATASET_ID"
            echo ""
            echo "Example query JSON structure:"
            echo '{
              "query": {
                "stages": [
                  {
                    "input": [{"inputName": "main", "datasetId": "o::'"$OBSERVE_CUSTOMER_ID"':dataset:DATASET_ID"}],
                    "stageID": "main",
                    "pipeline": "filter message ~ \"error\" | limit 10"
                  }
                ]
              }
            }'
            """,
            args=[],
            image="alpine:latest"
        )

    def execute_opal_query(self) -> ObserveCLITool:
        """Execute OPAL queries with AI-generated JSON query body."""
        return ObserveCLITool(
            name="observe_opal_query",
            description=(
                "Execute OPAL queries on Observe datasets. The AI should construct the complete JSON query body including dataset ID resolution. "
                "Use JQ to build the query JSON with proper dataset IDs, OPAL pipeline, and optional time parameters."
            ),
            content="""
            #!/bin/sh
            set -e
            
            # Validate environment
            if [ -z "$OBSERVE_API_KEY" ] || [ -z "$OBSERVE_CUSTOMER_ID" ]; then
                echo "❌ OBSERVE_API_KEY and OBSERVE_CUSTOMER_ID are required"
                exit 1
            fi
            
            # Install required tools
            apk add --no-cache jq curl >/dev/null 2>&1 || {
                echo "❌ Failed to install jq and curl"
                exit 1
            }
            
            # Parse arguments
            query="$query"
            interval="$interval"
            start_time="$start_time"
            end_time="$end_time"
            
            if [ -z "$query" ]; then
                echo "❌ query argument is required"
                echo ""
                echo "The query should be a complete JSON body with dataset IDs resolved."
                echo "Example structure:"
                echo '{
                  "query": {
                    "stages": [
                      {
                        "input": [{"inputName": "main", "datasetId": "o::CUSTOMER_ID:dataset:DATASET_ID"}],
                        "stageID": "main", 
                        "pipeline": "filter message ~ \"error\" | limit 10"
                      }
                    ]
                  }
                }'
                exit 1
            fi
            
            # Validate JSON
            if ! echo "$query" | jq empty 2>/dev/null; then
                echo "❌ Invalid JSON in query argument"
                echo "Received: $query"
                exit 1
            fi
            
            echo "📦 Query JSON:"
            echo "$query" | jq .
            echo ""
            
            # Build API URL with time parameters
            API_URL="https://$OBSERVE_CUSTOMER_ID.eu-1.observeinc.com/v1/meta/export/query"
            PARAMS=""
            
            if [ -n "$interval" ]; then
                PARAMS="interval=$interval"
            fi
            
            if [ -n "$start_time" ]; then
                if [ -n "$PARAMS" ]; then
                    PARAMS="$PARAMS&startTime=$start_time"
                else
                    PARAMS="startTime=$start_time"
                fi
            fi
            
            if [ -n "$end_time" ]; then
                if [ -n "$PARAMS" ]; then
                    PARAMS="$PARAMS&endTime=$end_time"
                else
                    PARAMS="endTime=$end_time"
                fi
            fi
            
            if [ -n "$PARAMS" ]; then
                API_URL="$API_URL?$PARAMS"
            fi
            
            echo "🚀 Executing OPAL query..."
            echo "URL: $API_URL"
            echo ""
            
            # Execute query
            RESPONSE=$(curl -s "$API_URL" \
                --request POST \
                --header "Authorization: Bearer $OBSERVE_CUSTOMER_ID $OBSERVE_API_KEY" \
                --header "Content-Type: application/json" \
                --header "Accept: application/x-ndjson" \
                --data "$query")
            
            # Process response
            if echo "$RESPONSE" | jq empty >/dev/null 2>&1; then
                echo "📊 Query Results:"
                echo "$RESPONSE" | jq .
                
                # Check for errors and provide guidance
                if echo "$RESPONSE" | jq -e '.error // .message' >/dev/null 2>&1; then
                    echo ""
                    echo "⚠️  Query completed with errors - see above for details"
                    
                    # Provide OPAL syntax help for common issues
                    if echo "$RESPONSE" | jq -r '.message // ""' | grep -q "expected one of"; then
                        echo ""
                        echo "💡 Common OPAL syntax tips:"
                        echo "  • Pattern matching: filter message ~ \"error\""
                        echo "  • Exact matching: filter severity == \"error\""
                        echo "  • Operators: ==, !=, ~, !~, <, >, contains"
                        echo "  • Piping: filter ... | limit 10 | pick_col timestamp, message"
                    fi
                fi
            else
                echo "📄 Raw response (non-JSON):"
                echo "$RESPONSE"
            fi
            """,
            args=[
                Arg(name="query", description="Complete JSON query body. Must include resolved dataset IDs in format 'o::CUSTOMER_ID:dataset:DATASET_ID'. Use JQ to construct: jq -n '{query: {stages: [{input: [{inputName: \"main\", datasetId: \"o::123:dataset:456\"}], stageID: \"main\", pipeline: \"filter message ~ \\\"error\\\" | limit 10\"}]}}'", required=True),
                Arg(name="interval", description="Time interval relative to now (e.g., '1h', '30m', '10s')", required=False),
                Arg(name="start_time", description="Start time as ISO timestamp (inclusive)", required=False),
                Arg(name="end_time", description="End time as ISO timestamp (exclusive)", required=False)
            ],
            image="alpine:latest"
        )


CLITools()