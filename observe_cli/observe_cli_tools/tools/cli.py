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
                self.execute_opal_query(),
                self.query_builder(),
                self.dataset_analyzer(),
                self.performance_monitor(),
                self.workspace_manager()
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
        """List datasets with advanced filtering and pagination support."""
        return ObserveCLITool(
            name="observe_list_datasets",
            description="List datasets with filtering, search, and pagination. Supports name filtering, type filtering, and result limiting for efficient data retrieval. Shows essential dataset information (ID, Name, Type).",
            content="""
            # Install required tools
            if ! command -v curl >/dev/null 2>&1; then
                apk add --no-cache curl >/dev/null 2>&1
            fi
            if ! command -v jq >/dev/null 2>&1; then
                apk add --no-cache jq >/dev/null 2>&1
            fi
            if ! command -v column >/dev/null 2>&1; then
                apk add --no-cache util-linux >/dev/null 2>&1
            fi
            
            # Validate environment
            if [ -z "$OBSERVE_API_KEY" ] || [ -z "$OBSERVE_CUSTOMER_ID" ]; then
                echo "Error: OBSERVE_API_KEY and OBSERVE_CUSTOMER_ID are required"
                exit 1
            fi
            
            # Build query parameters with defaults
            LIMIT=${limit:-10}
            OFFSET=${offset:-0}
            FORMAT=${output_format:-"table"}
            QUERY_PARAMS="limit=$LIMIT&offset=$OFFSET"
            
            # Add search filter if provided
            if [ -n "$name_filter" ]; then
                QUERY_PARAMS="${QUERY_PARAMS}&name=$name_filter"
            fi
            
            # Add type filter if provided
            if [ -n "$type_filter" ]; then
                QUERY_PARAMS="${QUERY_PARAMS}&type=$type_filter"
            fi
            
            echo "🔍 Fetching datasets (limit: $LIMIT, offset: $OFFSET)..."
            
            # Check cache first
            mkdir -p "/workspace/observe-data/cache"
            
            # Clean old cache files (older than 2 hours)
            find "/workspace/observe-data/cache" -name "datasets_*.json" -type f -mmin +120 -delete 2>/dev/null || true
            
            CACHE_KEY=$(echo "datasets_${LIMIT}_${OFFSET}_${name_filter}_${type_filter}_$(date +%Y%m%d%H)" | md5sum | cut -d' ' -f1)
            CACHE_FILE="/workspace/observe-data/cache/datasets_${CACHE_KEY}.json"
            
            # Check if cache file exists and is less than 30 minutes old
            CACHE_USED=false
            if [ -f "$CACHE_FILE" ]; then
                # Check if file is less than 30 minutes old (1800 seconds)
                FILE_AGE=$(( $(date +%s) - $(stat -c %Y "$CACHE_FILE" 2>/dev/null || echo 0) ))
                if [ "$FILE_AGE" -lt 1800 ]; then
                    echo "⚡ Using cached dataset list (cached $(($FILE_AGE/60)) minutes ago)"
                    RESPONSE=$(cat "$CACHE_FILE")
                    CACHE_USED=true
                fi
            fi
            
            # Make API call only if cache wasn't used
            if [ "$CACHE_USED" = "false" ]; then
                echo "🌐 Making API call..."
                RESPONSE=$(curl -s --max-time 30 --fail \
                    "https://$OBSERVE_CUSTOMER_ID.eu-1.observeinc.com/v1/dataset?$QUERY_PARAMS" \
                    --header "Authorization: Bearer $OBSERVE_CUSTOMER_ID $OBSERVE_API_KEY" \
                    --header "Content-Type: application/json" 2>/dev/null)
                
                CURL_EXIT_CODE=$?
                
                # Cache the response if successful
                if [ $CURL_EXIT_CODE -eq 0 ] && [ -n "$RESPONSE" ]; then
                    echo "$RESPONSE" > "$CACHE_FILE"
                    echo "💾 Dataset list cached to workspace: observe-data/cache/datasets_${CACHE_KEY}.json"
                else
                    echo "❌ API request failed. Check credentials and network connectivity."
                    exit 1
                fi
            fi
            
            # Validate response before parsing
            if [ -z "$RESPONSE" ]; then
                echo "❌ Empty response received from API"
                exit 1
            fi
            
            # Check if response is valid JSON
            if ! echo "$RESPONSE" | jq empty 2>/dev/null; then
                echo "❌ Invalid JSON response from API"
                echo "Raw response: $RESPONSE"
                exit 1
            fi
            
            # Parse and format response based on format
            if [ "$FORMAT" = "table" ]; then
                DATASET_COUNT=$(echo "$RESPONSE" | jq -r '.data | length // 0')
                echo "📊 Found $DATASET_COUNT datasets:"
                echo ""
                echo "ID           | NAME                                           | TYPE"
                echo "-------------|-----------------------------------------------|----------"
                echo "$RESPONSE" | jq -r '
                    if .data then
                        .data[] | 
                        (.meta.id | split(":") | last) + " | " + .config.name + " | " + .state.kind
                    else
                        "No datasets found"
                    end'
                echo ""
                echo "💡 Tip: Use --limit to see more datasets (e.g., --limit 50) or --name_filter to search for specific datasets"
            elif [ "$FORMAT" = "json" ]; then
                echo "$RESPONSE" | jq '.' 2>/dev/null || echo "Error: Invalid JSON response"
            elif [ "$FORMAT" = "compact" ]; then
                echo "$RESPONSE" | jq -r '
                    if .data then
                        .data[] | "\(.meta.id | split(":") | last): \(.config.name) (\(.state.kind))"
                    else
                        "No datasets found"
                    end'
            else
                echo "$RESPONSE" | jq -r '
                    if .data then
                        "Found \(.data | length) datasets:\n" +
                        (.data[] | "• \(.config.name) [\(.meta.id | split(":") | last)] - \(.state.kind)")
                    else
                        "No datasets found"
                    end'
            fi
            """,
            args=[
                Arg(name="limit", description="Maximum number of datasets to return (default: 10, max: 500)", required=False),
                Arg(name="offset", description="Number of datasets to skip for pagination (default: 0)", required=False),
                Arg(name="name_filter", description="Filter datasets by name (partial match)", required=False),
                Arg(name="type_filter", description="Filter by dataset type (e.g., 'logs', 'metrics', 'events')", required=False),
                Arg(name="output_format", description="Output format: table, json, compact, summary (default: table)", required=False)
            ],
            image="alpine:latest"
        )

    def execute_opal_query(self) -> ObserveCLITool:
        """Execute optimized OPAL queries with intelligent filtering and caching."""
        return ObserveCLITool(
            name="observe_opal_query",
            description="Execute high-performance OPAL queries with smart filtering, result limiting, caching, and multiple output formats. Includes query optimization and performance monitoring.",
            content="""
            # Install dependencies
            if ! command -v curl >/dev/null 2>&1; then apk add --no-cache curl; fi
            if ! command -v jq >/dev/null 2>&1; then apk add --no-cache jq; fi
            if ! command -v date >/dev/null 2>&1; then apk add --no-cache coreutils; fi
            
            # Validate inputs
            if [ -z "$OBSERVE_API_KEY" ] || [ -z "$OBSERVE_CUSTOMER_ID" ] || [ -z "$dataset_id" ] || [ -z "$opal_query" ]; then
                echo "❌ Missing required parameters: OBSERVE_API_KEY, OBSERVE_CUSTOMER_ID, dataset_id, opal_query"
                exit 1
            fi
            
            # Performance defaults and limits
            MAX_ROWS=${max_rows:-1000}
            TIMEOUT=${timeout:-60}
            OUTPUT_FORMAT=${output_format:-"table"}
            CACHE_RESULTS=${cache_results:-"true"}
            
            # Smart query optimization - automatically add limits if not present
            OPTIMIZED_QUERY="$opal_query"
            if ! echo "$OPTIMIZED_QUERY" | grep -q "limit"; then
                OPTIMIZED_QUERY="$OPTIMIZED_QUERY | limit $MAX_ROWS"
            fi
            
            # Add performance-oriented columns if select/pick_col not specified
            if ! echo "$OPTIMIZED_QUERY" | grep -qE "(pick_col|select|fields)"; then
                OPTIMIZED_QUERY="pick_col TIMESTAMP, * | $OPTIMIZED_QUERY"
            fi
            
            echo "🚀 Executing optimized query (max rows: $MAX_ROWS, timeout: ${TIMEOUT}s)..."
            echo "🔍 Query: $OPTIMIZED_QUERY"
            
            # Build optimized payload with compression
            QUERY_PAYLOAD=$(jq -n \
                --arg dataset_id "$dataset_id" \
                --arg pipeline "$OPTIMIZED_QUERY" \
                '{
                    "query": {
                        "stages": [{
                            "input": [{"datasetId": $dataset_id}],
                            "stageID": "main",
                            "pipeline": $pipeline
                        }]
                    },
                    "maxRows": '${MAX_ROWS}',
                    "format": "json",
                    "compression": "gzip"
                }')
            
            # Build time parameters with smart defaults
            QUERY_PARAMS=""
            if [ -n "$start_time" ]; then
                QUERY_PARAMS="startTime=$start_time"
            elif [ -n "$time_range" ]; then
                # Convert relative time to absolute timestamps
                case "$time_range" in
                    "1h"|"hour") 
                        START_TIME=$(date -d "1 hour ago" -u +"%Y-%m-%dT%H:%M:%SZ")
                        QUERY_PARAMS="startTime=$START_TIME" ;;
                    "24h"|"day")
                        START_TIME=$(date -d "1 day ago" -u +"%Y-%m-%dT%H:%M:%SZ")
                        QUERY_PARAMS="startTime=$START_TIME" ;;
                    "7d"|"week")
                        START_TIME=$(date -d "1 week ago" -u +"%Y-%m-%dT%H:%M:%SZ")
                        QUERY_PARAMS="startTime=$START_TIME" ;;
                esac
            fi
            
            if [ -n "$end_time" ]; then
                QUERY_PARAMS="${QUERY_PARAMS}&endTime=$end_time"
            fi
            
            # Build URL with parameters
            URL="https://$OBSERVE_CUSTOMER_ID.eu-1.observeinc.com/v1/meta/export/query"
            if [ -n "$QUERY_PARAMS" ]; then
                URL="$URL?$QUERY_PARAMS"
            fi
            
            # Execute with performance monitoring
            START_TIME=$(date +%s)
            
            RESPONSE=$(curl -s --max-time "$TIMEOUT" --fail \
                --compressed \
                --header "Authorization: Bearer $OBSERVE_CUSTOMER_ID $OBSERVE_API_KEY" \
                --header "Content-Type: application/json" \
                --header "Accept-Encoding: gzip" \
                --request POST \
                --data "$QUERY_PAYLOAD" \
                "$URL" 2>/dev/null)
            
            CURL_EXIT_CODE=$?
            END_TIME=$(date +%s)
            EXECUTION_TIME=$((END_TIME - START_TIME))
            
            if [ $CURL_EXIT_CODE -ne 0 ]; then
                echo "❌ Query failed (exit code: $CURL_EXIT_CODE). Check dataset ID, query syntax, and network connectivity."
                exit 1
            fi
            
            # Parse and format results intelligently
            if [ -z "$RESPONSE" ]; then
                echo "⚠️ Empty response received"
                exit 1
            fi
            
            echo "✅ Query completed in ${EXECUTION_TIME}s"
            
            case "$OUTPUT_FORMAT" in
                "table")
                    echo "$RESPONSE" | jq -r '
                        if .data and (.data | length > 0) then
                            (.data[0] | keys_unsorted) as $keys |
                            ($keys | @csv),
                            (.data[] | [.[$keys[]]] | @csv)
                        else
                            "No results found"
                        end' | head -n $((MAX_ROWS + 1)) | column -t -s ','
                    ;;
                "json")
                    echo "$RESPONSE" | jq -r '
                        if .data then
                            {"results": .data, "count": (.data | length), "execution_time": "'${EXECUTION_TIME}'s"}
                        else
                            {"error": "No data returned", "execution_time": "'${EXECUTION_TIME}'s"}
                        end'
                    ;;
                "csv")
                    echo "$RESPONSE" | jq -r '
                        if .data and (.data | length > 0) then
                            (.data[0] | keys_unsorted) as $keys |
                            ($keys | @csv),
                            (.data[] | [.[$keys[]]] | @csv)
                        else
                            "No results found"
                        end'
                    ;;
                "summary")
                    echo "$RESPONSE" | jq -r '
                        if .data then
                            "Results: " + (.data | length | tostring) + " rows\n" +
                            "Execution: '${EXECUTION_TIME}'s\n" +
                            "Query: '${OPTIMIZED_QUERY}'\n" +
                            if (.data | length > 0) then
                                "Fields: " + (.data[0] | keys | join(", "))
                            else
                                "No data returned"
                            end
                        else
                            "Error: No data in response"
                        end'
                    ;;
                *)
                    echo "$RESPONSE" | jq '.'
                    ;;
            esac
            
            # Cache results by default in workspace volume
            if [ "$CACHE_RESULTS" = "true" ]; then
                # Create cache directory if it doesn't exist
                mkdir -p "/workspace/observe-data/cache"
                
                CACHE_KEY=$(echo "${dataset_id}_${OPTIMIZED_QUERY}_$(date +%Y%m%d)" | md5sum | cut -d' ' -f1)
                CACHE_FILE="/workspace/observe-data/cache/query_${CACHE_KEY}.json"
                
                # Check if cache exists and is recent (within 1 hour)
                if [ -f "$CACHE_FILE" ] && [ $(find "$CACHE_FILE" -mmin -60 | wc -l) -gt 0 ]; then
                    echo "⚡ Using cached results from: query_${CACHE_KEY}.json"
                    cat "$CACHE_FILE"
                    exit 0
                fi
                
                # Save new results to cache
                echo "$RESPONSE" > "$CACHE_FILE"
                echo "💾 Results cached to workspace: observe-data/cache/query_${CACHE_KEY}.json"
                
                # Clean old cache files (older than 7 days)
                find "/workspace/observe-data/cache" -name "query_*.json" -mtime +7 -delete 2>/dev/null || true
            fi
            """,
            args=[
                Arg(name="dataset_id", description="Dataset ID to query (e.g., 41000001)", required=True),
                Arg(name="opal_query", description="OPAL query pipeline (e.g., 'filter level==\"ERROR\" | top 10 by count')", required=True),
                Arg(name="max_rows", description="Maximum rows to return (default: 1000, helps prevent overwhelming output)", required=False),
                Arg(name="output_format", description="Output format: table, json, csv, summary (default: table)", required=False),
                Arg(name="time_range", description="Relative time range: 1h, 24h, 7d (alternative to start_time)", required=False),
                Arg(name="start_time", description="Start time in ISO8601 format (e.g., 2023-04-20T16:20:00Z)", required=False),
                Arg(name="end_time", description="End time in ISO8601 format (e.g., 2023-04-20T16:30:00Z)", required=False),
                Arg(name="timeout", description="Query timeout in seconds (default: 60)", required=False),
                Arg(name="cache_results", description="Cache results for reuse: true/false (default: true)", required=False)
            ],
            image="alpine:latest"
        )

    def query_builder(self) -> ObserveCLITool:
        """Interactive query builder with templates and validation."""
        return ObserveCLITool(
            name="observe_query_builder",
            description="Build optimized OPAL queries using templates, validation, and smart suggestions. Includes common patterns for logs, metrics, and security analysis.",
            content="""
            # Install dependencies
            if ! command -v jq >/dev/null 2>&1; then apk add --no-cache jq; fi
            
            echo "🔧 OPAL Query Builder & Optimizer"
            echo "=================================="
            
            QUERY_TYPE=${query_type:-"custom"}
            DATASET_ID=${dataset_id:-""}
            
            case "$QUERY_TYPE" in
                "error_analysis")
                    TEMPLATE='filter level == "ERROR" or severity == "error" | pick_col TIMESTAMP, message, host, level | top 50 by TIMESTAMP desc'
                    echo "📊 Error Analysis Template:"
                    ;;
                "performance_monitoring") 
                    TEMPLATE='filter response_time > 1000 or duration > "1s" | pick_col TIMESTAMP, response_time, endpoint, user_id | stats avg(response_time) by endpoint | sort avg_response_time desc'
                    echo "⚡ Performance Monitoring Template:"
                    ;;
                "security_events")
                    TEMPLATE='filter action == "login" or event_type == "authentication" | pick_col TIMESTAMP, user_id, source_ip, action, result | filter result == "failed" | top 100 by TIMESTAMP desc'
                    echo "🔒 Security Events Template:"
                    ;;
                "resource_usage")
                    TEMPLATE='pick_col TIMESTAMP, cpu_usage, memory_usage, host | filter cpu_usage > 80 or memory_usage > 85 | stats max(cpu_usage), max(memory_usage) by host'
                    echo "💻 Resource Usage Template:"
                    ;;
                "log_aggregation")
                    TEMPLATE='pick_col TIMESTAMP, level, message, service | filter level in ("WARN", "ERROR", "FATAL") | stats count by level, service | sort count desc'
                    echo "📝 Log Aggregation Template:"
                    ;;
                *)
                    if [ -n "$custom_query" ]; then
                        TEMPLATE="$custom_query"
                        echo "✏️  Custom Query:"
                    else
                        echo "❌ No query specified. Use query_type parameter or provide custom_query."
                        exit 1
                    fi
                    ;;
            esac
            
            echo "Query: $TEMPLATE"
            echo ""
            
            # Query validation and optimization
            echo "🔍 Query Analysis:"
            
            # Check for common performance issues
            if ! echo "$TEMPLATE" | grep -q "limit"; then
                echo "⚠️  No LIMIT clause - adding default limit of 1000 for performance"
                TEMPLATE="$TEMPLATE | limit 1000"
            fi
            
            if ! echo "$TEMPLATE" | grep -q "pick_col"; then
                echo "💡 Consider using pick_col to select specific fields for better performance"
            fi
            
            if echo "$TEMPLATE" | grep -q "stats.*by.*stats"; then
                echo "⚠️  Multiple stats operations detected - consider combining for efficiency"
            fi
            
            # Time range recommendations
            if [ -z "$time_range" ] && [ -z "$start_time" ]; then
                echo "💡 No time range specified - defaulting to last 24 hours for performance"
                TIME_SUGGESTION="--time_range 24h"
            else
                TIME_SUGGESTION=""
            fi
            
            echo ""
            echo "✅ Optimized Query Ready:"
            echo "$TEMPLATE"
            echo ""
            
            if [ -n "$DATASET_ID" ]; then
                echo "🚀 Execute with:"
                echo "observe_opal_query --dataset_id $DATASET_ID --opal_query \"$TEMPLATE\" $TIME_SUGGESTION"
            else
                echo "📋 To execute, use:"
                echo "observe_opal_query --dataset_id YOUR_DATASET_ID --opal_query \"$TEMPLATE\" $TIME_SUGGESTION"
            fi
            
            # Save template by default to workspace volume
            SAVE_TEMPLATE=${save_template:-"true"}
            if [ "$SAVE_TEMPLATE" = "true" ]; then
                mkdir -p "/workspace/observe-data/templates"
                TEMPLATE_NAME="${query_type:-custom}_$(date +%Y%m%d_%H%M%S).opal"
                TEMPLATE_FILE="/workspace/observe-data/templates/$TEMPLATE_NAME"
                echo "$TEMPLATE" > "$TEMPLATE_FILE"
                echo ""
                echo "💾 Template saved to workspace: observe-data/templates/$TEMPLATE_NAME"
                
                # Also create a templates index file
                INDEX_FILE="/workspace/observe-data/templates/index.json"
                if [ ! -f "$INDEX_FILE" ]; then
                    echo "[]" > "$INDEX_FILE"
                fi
                
                # Add template info to index
                jq --arg name "$TEMPLATE_NAME" \
                   --arg type "$QUERY_TYPE" \
                   --arg query "$TEMPLATE" \
                   --arg timestamp "$(date -Iseconds)" \
                   '. += [{"name": $name, "type": $type, "query": $query, "created": $timestamp}]' \
                   "$INDEX_FILE" > "${INDEX_FILE}.tmp" && mv "${INDEX_FILE}.tmp" "$INDEX_FILE"
                
                echo "📋 Template indexed for easy retrieval"
            fi
            """,
            args=[
                Arg(name="query_type", description="Template type: error_analysis, performance_monitoring, security_events, resource_usage, log_aggregation, custom", required=False),
                Arg(name="custom_query", description="Custom OPAL query (used with query_type=custom)", required=False),
                Arg(name="dataset_id", description="Dataset ID for immediate execution suggestions", required=False),
                Arg(name="time_range", description="Suggested time range for the query", required=False),
                Arg(name="save_template", description="Save generated template to file (true/false)", required=False)
            ],
            image="alpine:latest"
        )

    def dataset_analyzer(self) -> ObserveCLITool:
        """Analyze dataset structure, performance, and optimization opportunities."""
        return ObserveCLITool(
            name="observe_dataset_analyzer", 
            description="Deep analysis of dataset structure, field distribution, performance metrics, and optimization recommendations. Provides insights for better query performance.",
            content="""
            # Install dependencies
            if ! command -v curl >/dev/null 2>&1; then apk add --no-cache curl; fi
            if ! command -v jq >/dev/null 2>&1; then apk add --no-cache jq; fi
            
            # Validate inputs
            if [ -z "$OBSERVE_API_KEY" ] || [ -z "$OBSERVE_CUSTOMER_ID" ] || [ -z "$dataset_id" ]; then
                echo "❌ Missing required parameters: OBSERVE_API_KEY, OBSERVE_CUSTOMER_ID, dataset_id"
                exit 1
            fi
            
            echo "🔬 Dataset Analysis Report"
            echo "========================="
            echo "Dataset ID: $dataset_id"
            echo "Timestamp: $(date)"
            echo ""
            
            # Get dataset metadata
            echo "📊 Fetching dataset metadata..."
            DATASET_INFO=$(curl -s --max-time 30 --fail \
                "https://$OBSERVE_CUSTOMER_ID.eu-1.observeinc.com/v1/dataset/$dataset_id" \
                --header "Authorization: Bearer $OBSERVE_CUSTOMER_ID $OBSERVE_API_KEY" \
                --header "Content-Type: application/json" 2>/dev/null)
            
            if [ $? -ne 0 ]; then
                echo "❌ Failed to fetch dataset metadata"
                exit 1
            fi
            
            # Basic dataset info
            echo "📋 Dataset Information:"
            echo "$DATASET_INFO" | jq -r '
                "Name: " + (.name // "Unknown"),
                "Type: " + (.kind // "Unknown"), 
                "Status: " + (.status // "Unknown"),
                "Record Count: " + ((.recordCount // 0) | tostring),
                "Size: " + ((.sizeBytes // 0) | tostring) + " bytes"
            '
            echo ""
            
            # Analyze field structure with sample query
            echo "🔍 Analyzing field structure..."
            SAMPLE_QUERY='pick_col * | limit 5'
            SAMPLE_PAYLOAD=$(jq -n \
                --arg dataset_id "$dataset_id" \
                --arg pipeline "$SAMPLE_QUERY" \
                '{
                    "query": {
                        "stages": [{
                            "input": [{"datasetId": $dataset_id}],
                            "stageID": "main", 
                            "pipeline": $pipeline
                        }]
                    }
                }')
            
            SAMPLE_DATA=$(curl -s --max-time 30 --fail \
                "https://$OBSERVE_CUSTOMER_ID.eu-1.observeinc.com/v1/meta/export/query" \
                --header "Authorization: Bearer $OBSERVE_CUSTOMER_ID $OBSERVE_API_KEY" \
                --header "Content-Type: application/json" \
                --request POST \
                --data "$SAMPLE_PAYLOAD" 2>/dev/null)
            
            if [ $? -eq 0 ] && [ -n "$SAMPLE_DATA" ]; then
                echo "📝 Field Analysis:"
                echo "$SAMPLE_DATA" | jq -r '
                    if .data and (.data | length > 0) then
                        (.data[0] | keys) as $fields |
                        "Total Fields: " + ($fields | length | tostring) + "\n" +
                        "Available Fields:" + 
                        ($fields | map("  • " + .) | join("\n"))
                    else
                        "No sample data available for field analysis"
                    end
                '
                echo ""
                
                # Performance recommendations based on field analysis
                echo "⚡ Performance Recommendations:"
                echo "$SAMPLE_DATA" | jq -r '
                    if .data and (.data | length > 0) then
                        (.data[0] | keys) as $fields |
                        (
                            if ($fields | map(select(test("timestamp|time|date"; "i"))) | length > 0) then
                                "✅ Time-based fields detected - time filtering will be efficient"
                            else
                                "⚠️  No obvious timestamp fields - consider adding time filters"
                            end
                        ) + "\n" +
                        (
                            if ($fields | length > 20) then
                                "💡 High field count (" + ($fields | length | tostring) + ") - use pick_col to select specific fields"
                            else
                                "✅ Reasonable field count (" + ($fields | length | tostring) + ") - pick_col still recommended"
                            end
                        ) + "\n" +
                        (
                            if ($fields | map(select(test("level|severity|priority"; "i"))) | length > 0) then
                                "✅ Log level fields detected - filtering by severity will be efficient"
                            else
                                "💡 Consider filtering by categorical fields for better performance"
                            end
                        )
                    else
                        "Unable to provide recommendations without sample data"
                    end
                '
            else
                echo "⚠️ Unable to fetch sample data for field analysis"
            fi
            
            echo ""
            echo "📈 Query Optimization Tips:"
            echo "• Always use 'limit' to prevent overwhelming results"
            echo "• Use 'pick_col' to select only needed fields" 
            echo "• Filter early in your pipeline for better performance"
            echo "• Use time-based filters when possible"
            echo "• Consider using 'stats' for aggregations over raw data"
            echo "• Test queries with small limits first, then scale up"
            echo ""
            
            # Generate sample optimized queries
            echo "🚀 Sample Optimized Queries:"
            echo ""
            echo "# Basic exploration (safe for any dataset):"
            echo "pick_col * | limit 10"
            echo ""
            echo "# Time-filtered analysis (last hour):"
            echo "filter TIMESTAMP > @\"1 hour ago\" | pick_col TIMESTAMP, * | limit 100"
            echo ""
            echo "# Aggregated view:"
            echo "pick_col TIMESTAMP, level | stats count by level | sort count desc"
            """,
            args=[
                Arg(name="dataset_id", description="Dataset ID to analyze (e.g., 41000001)", required=True)
            ],
            image="alpine:latest"
        )

    def performance_monitor(self) -> ObserveCLITool:
        """Monitor query performance and system health."""
        return ObserveCLITool(
            name="observe_performance_monitor",
            description="Monitor Observe API performance, track query execution times, and provide system health insights. Includes performance benchmarking and optimization tracking.",
            content="""
            # Install dependencies
            if ! command -v curl >/dev/null 2>&1; then apk add --no-cache curl; fi
            if ! command -v jq >/dev/null 2>&1; then apk add --no-cache jq; fi
            
            echo "📊 Observe Performance Monitor"
            echo "============================="
            echo "Started: $(date)"
            echo ""
            
            # Validate connection
            if [ -z "$OBSERVE_API_KEY" ] || [ -z "$OBSERVE_CUSTOMER_ID" ]; then
                echo "❌ Missing credentials"
                exit 1
            fi
            
            # API Health Check
            echo "🏥 API Health Check:"
            START_TIME=$(date +%s%3N)
            
            HEALTH_RESPONSE=$(curl -s --max-time 10 --fail \
                "https://$OBSERVE_CUSTOMER_ID.eu-1.observeinc.com/v1/dataset?limit=1" \
                --header "Authorization: Bearer $OBSERVE_CUSTOMER_ID $OBSERVE_API_KEY" \
                --header "Content-Type: application/json" 2>/dev/null)
            
            HEALTH_EXIT_CODE=$?
            END_TIME=$(date +%s%3N)
            API_LATENCY=$((END_TIME - START_TIME))
            
            if [ $HEALTH_EXIT_CODE -eq 0 ]; then
                echo "✅ API Status: Healthy"
                echo "⚡ Response Time: ${API_LATENCY}ms"
            else
                echo "❌ API Status: Unhealthy (exit code: $HEALTH_EXIT_CODE)"
                echo "🔍 Check credentials and network connectivity"
                exit 1
            fi
            
            # Performance benchmark if requested
            if [ "$run_benchmark" = "true" ]; then
                echo ""
                echo "🏁 Performance Benchmark:"
                
                # Benchmark different query sizes
                for LIMIT in 10 100 1000; do
                    echo "Testing query with limit $LIMIT..."
                    
                    if [ -n "$dataset_id" ]; then
                        START_TIME=$(date +%s%3N)
                        
                        BENCHMARK_PAYLOAD=$(jq -n \
                            --arg dataset_id "$dataset_id" \
                            --arg limit "$LIMIT" \
                            '{
                                "query": {
                                    "stages": [{
                                        "input": [{"datasetId": $dataset_id}],
                                        "stageID": "main",
                                        "pipeline": ("pick_col TIMESTAMP, * | limit " + $limit)
                                    }]
                                }
                            }')
                        
                        BENCHMARK_RESPONSE=$(curl -s --max-time 60 --fail \
                            "https://$OBSERVE_CUSTOMER_ID.eu-1.observeinc.com/v1/meta/export/query" \
                            --header "Authorization: Bearer $OBSERVE_CUSTOMER_ID $OBSERVE_API_KEY" \
                            --header "Content-Type: application/json" \
                            --request POST \
                            --data "$BENCHMARK_PAYLOAD" 2>/dev/null)
                        
                        END_TIME=$(date +%s%3N)
                        QUERY_LATENCY=$((END_TIME - START_TIME))
                        
                        if [ $? -eq 0 ]; then
                            RESULT_COUNT=$(echo "$BENCHMARK_RESPONSE" | jq -r '.data | length // 0')
                            echo "  ✅ Limit $LIMIT: ${QUERY_LATENCY}ms (${RESULT_COUNT} rows)"
                        else
                            echo "  ❌ Limit $LIMIT: Failed"
                        fi
                    else
                        echo "  ⚠️ Skipping query benchmark - no dataset_id provided"
                        break
                    fi
                done
            fi
            
            # System recommendations
            echo ""
            echo "💡 Performance Recommendations:"
            
            if [ $API_LATENCY -gt 2000 ]; then
                echo "⚠️ High API latency (${API_LATENCY}ms) - consider:"
                echo "  • Using smaller result sets"
                echo "  • Adding more specific filters"
                echo "  • Checking network connectivity"
            elif [ $API_LATENCY -gt 1000 ]; then
                echo "⚠️ Moderate API latency (${API_LATENCY}ms) - monitor performance"
            else
                echo "✅ Good API latency (${API_LATENCY}ms)"
            fi
            
            echo ""
            echo "🎯 Best Practices:"
            echo "• Start queries with small limits (10-100 rows)"
            echo "• Use time-based filtering for recent data"
            echo "• Pick specific columns with pick_col"
            echo "• Monitor execution times and adjust accordingly"
            echo "• Cache frequently used query results"
            
            # Save performance log by default to workspace volume
            SAVE_METRICS=${save_metrics:-"true"}
            if [ "$SAVE_METRICS" = "true" ]; then
                mkdir -p "/workspace/observe-data/metrics"
                METRICS_FILE="/workspace/observe-data/metrics/performance_$(date +%Y%m%d_%H%M%S).json"
                jq -n \
                    --arg timestamp "$(date -Iseconds)" \
                    --arg api_latency "$API_LATENCY" \
                    --arg api_status "$HEALTH_EXIT_CODE" \
                    '{
                        "timestamp": $timestamp,
                        "api_latency_ms": ($api_latency | tonumber),
                        "api_healthy": ($api_status == "0"),
                        "customer_id": "'$OBSERVE_CUSTOMER_ID'"
                    }' > "$METRICS_FILE"
                echo ""
                echo "📊 Performance metrics saved to workspace: observe-data/metrics/performance_$(date +%Y%m%d_%H%M%S).json"
                
                # Clean old metrics files (older than 30 days)
                find "/workspace/observe-data/metrics" -name "performance_*.json" -mtime +30 -delete 2>/dev/null || true
            fi
            """,
            args=[
                Arg(name="dataset_id", description="Dataset ID for query benchmarking (optional)", required=False),
                Arg(name="run_benchmark", description="Run performance benchmark tests (true/false)", required=False),
                Arg(name="save_metrics", description="Save performance metrics to file (true/false)", required=False)
            ],
            image="alpine:latest"
        )

    def workspace_manager(self) -> ObserveCLITool:
        """Manage cached data, templates, and workspace cleanup."""
        return ObserveCLITool(
            name="observe_workspace_manager",
            description="Manage Observe workspace data including cache, templates, metrics, and cleanup operations. View cached queries, saved templates, and performance history.",
            content="""
            # Install dependencies
            if ! command -v jq >/dev/null 2>&1; then apk add --no-cache jq; fi
            
            ACTION=${action:-"status"}
            
            echo "🗂️  Observe Workspace Manager"
            echo "============================"
            echo "Workspace: /workspace/observe-data"
            echo ""
            
            # Create directories if they don't exist
            mkdir -p "/workspace/observe-data/cache"
            mkdir -p "/workspace/observe-data/templates" 
            mkdir -p "/workspace/observe-data/metrics"
            
            case "$ACTION" in
                "status"|"info")
                    echo "📊 Workspace Status:"
                    echo "==================="
                    
                    # Cache information
                    CACHE_COUNT=$(find /workspace/observe-data/cache -name "*.json" -type f 2>/dev/null | wc -l)
                    CACHE_SIZE=$(du -sh /workspace/observe-data/cache 2>/dev/null | cut -f1 || echo "0B")
                    echo "🗄️  Cache: $CACHE_COUNT files ($CACHE_SIZE)"
                    
                    # Templates information
                    TEMPLATE_COUNT=$(find /workspace/observe-data/templates -name "*.opal" -type f 2>/dev/null | wc -l)
                    TEMPLATE_SIZE=$(du -sh /workspace/observe-data/templates 2>/dev/null | cut -f1 || echo "0B")
                    echo "📋 Templates: $TEMPLATE_COUNT files ($TEMPLATE_SIZE)"
                    
                    # Metrics information
                    METRICS_COUNT=$(find /workspace/observe-data/metrics -name "*.json" -type f 2>/dev/null | wc -l)
                    METRICS_SIZE=$(du -sh /workspace/observe-data/metrics 2>/dev/null | cut -f1 || echo "0B")
                    echo "📈 Metrics: $METRICS_COUNT files ($METRICS_SIZE)"
                    
                    # Total size
                    TOTAL_SIZE=$(du -sh /workspace/observe-data 2>/dev/null | cut -f1 || echo "0B")
                    echo "💾 Total workspace size: $TOTAL_SIZE"
                    ;;
                
                "list-cache")
                    echo "🗄️  Cache Files:"
                    echo "==============="
                    find /workspace/observe-data/cache -name "*.json" -type f -exec basename {} \; 2>/dev/null | sort || echo "No cache files found"
                    echo ""
                    echo "Recent cache files (last 24 hours):"
                    find /workspace/observe-data/cache -name "*.json" -type f -mtime -1 -exec ls -lh {} \; 2>/dev/null | awk '{print $9, $5, $6, $7, $8}' || echo "No recent cache files"
                    ;;
                
                "list-templates")
                    echo "📋 Template Files:"
                    echo "=================="
                    if [ -f "/workspace/observe-data/templates/index.json" ]; then
                        jq -r '.[] | "• \(.name) (\(.type)) - \(.created)"' /workspace/observe-data/templates/index.json 2>/dev/null || echo "No templates index found"
                    else
                        find /workspace/observe-data/templates -name "*.opal" -type f -exec basename {} \; 2>/dev/null | sort || echo "No template files found"
                    fi
                    ;;
                
                "list-metrics")
                    echo "📈 Performance Metrics:"
                    echo "======================"
                    find /workspace/observe-data/metrics -name "*.json" -type f -exec basename {} \; 2>/dev/null | sort -r | head -10 || echo "No metrics files found"
                    echo ""
                    if [ -n "$(find /workspace/observe-data/metrics -name "*.json" -type f 2>/dev/null)" ]; then
                        echo "Latest performance summary:"
                        LATEST_METRIC=$(find /workspace/observe-data/metrics -name "*.json" -type f -newest 2>/dev/null | head -1)
                        if [ -n "$LATEST_METRIC" ]; then
                            jq -r '"Timestamp: " + .timestamp + ", API Latency: " + (.api_latency_ms | tostring) + "ms, Status: " + (if .api_healthy then "✅ Healthy" else "❌ Unhealthy" end)' "$LATEST_METRIC" 2>/dev/null || echo "Unable to parse latest metric"
                        fi
                    fi
                    ;;
                
                "cleanup")
                    echo "🧹 Workspace Cleanup:"
                    echo "===================="
                    
                    # Clean old cache files (older than 7 days)
                    CACHE_CLEANED=$(find /workspace/observe-data/cache -name "*.json" -type f -mtime +7 -delete -print 2>/dev/null | wc -l)
                    echo "🗄️  Cleaned $CACHE_CLEANED old cache files (>7 days)"
                    
                    # Clean old metrics files (older than 30 days)
                    METRICS_CLEANED=$(find /workspace/observe-data/metrics -name "*.json" -type f -mtime +30 -delete -print 2>/dev/null | wc -l)
                    echo "📈 Cleaned $METRICS_CLEANED old metrics files (>30 days)"
                    
                    # Template cleanup is manual to avoid accidental deletion
                    TEMPLATE_OLD=$(find /workspace/observe-data/templates -name "*.opal" -type f -mtime +90 2>/dev/null | wc -l)
                    if [ $TEMPLATE_OLD -gt 0 ]; then
                        echo "📋 Found $TEMPLATE_OLD old templates (>90 days) - use 'cleanup-templates' to remove"
                    else
                        echo "📋 No old templates to clean"
                    fi
                    ;;
                
                "cleanup-templates")
                    echo "🧹 Template Cleanup:"
                    echo "==================="
                    TEMPLATE_CLEANED=$(find /workspace/observe-data/templates -name "*.opal" -type f -mtime +90 -delete -print 2>/dev/null | wc -l)
                    echo "📋 Cleaned $TEMPLATE_CLEANED old template files (>90 days)"
                    
                    # Rebuild index
                    if [ -f "/workspace/observe-data/templates/index.json" ]; then
                        echo '[]' > "/workspace/observe-data/templates/index.json"
                        echo "📋 Template index reset - will be rebuilt on next template creation"
                    fi
                    ;;
                
                "clear-cache")
                    echo "🧹 Cache Clear:"
                    echo "==============="
                    CACHE_CLEARED=$(find /workspace/observe-data/cache -name "*.json" -type f -delete -print 2>/dev/null | wc -l)
                    echo "🗄️  Cleared $CACHE_CLEARED cache files"
                    ;;
                
                *)
                    echo "❌ Unknown action: $ACTION"
                    echo ""
                    echo "Available actions:"
                    echo "• status/info - Show workspace status"
                    echo "• list-cache - List cached query files"
                    echo "• list-templates - List saved templates"
                    echo "• list-metrics - List performance metrics"
                    echo "• cleanup - Clean old cache and metrics files"
                    echo "• cleanup-templates - Clean old template files"
                    echo "• clear-cache - Clear all cache files"
                    ;;
            esac
            """,
            args=[
                Arg(name="action", description="Action to perform: status, list-cache, list-templates, list-metrics, cleanup, cleanup-templates, clear-cache", required=False)
            ],
            image="alpine:latest"
        )

CLITools()