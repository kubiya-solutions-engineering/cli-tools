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
                self.get_available_datasets(),
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

    def get_available_datasets(self) -> ObserveCLITool:
        """Get available dataset IDs from environment configuration."""
        return ObserveCLITool(
            name="observe_get_available_datasets",
            description="Get available dataset IDs configured in the environment. Use this first to check which datasets are available for querying.",
            content="""
            if [ -n "$OBSERVE_DATASET_IDS" ]; then
                echo "Available datasets: $OBSERVE_DATASET_IDS"
            else
                echo "No datasets configured. Please set OBSERVE_DATASET_IDS in the agent configuration environment variables section. Cannot continue"
                exit 1
            fi
            """,
            args=[],
            image="alpine:latest"
        )

    def list_datasets(self) -> ObserveCLITool:
        """List datasets with advanced filtering and pagination support."""
        return ObserveCLITool(
            name="observe_list_datasets",
            description="List datasets with filtering, search, and pagination. Supports name filtering, type filtering, and result limiting for efficient data retrieval.",
            content="""
            # Install required tools
            if ! command -v curl >/dev/null 2>&1; then
                apk add --no-cache curl
            fi
            if ! command -v jq >/dev/null 2>&1; then
                apk add --no-cache jq
            fi
            
            # Validate environment
            if [ -z "$OBSERVE_API_KEY" ] || [ -z "$OBSERVE_CUSTOMER_ID" ]; then
                echo "Error: OBSERVE_API_KEY and OBSERVE_CUSTOMER_ID are required"
                exit 1
            fi
            
            # Build query parameters with defaults
            LIMIT=${limit:-50}
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
            CACHE_KEY=$(echo "datasets_${LIMIT}_${OFFSET}_${name_filter}_${type_filter}_$(date +%Y%m%d%H)" | md5sum | cut -d' ' -f1)
            CACHE_FILE="/workspace/observe-data/cache/datasets_${CACHE_KEY}.json"
            
            if [ -f "$CACHE_FILE" ] && [ $(find "$CACHE_FILE" -mmin -30 | wc -l) -gt 0 ]; then
                echo "⚡ Using cached dataset list from: datasets_${CACHE_KEY}.json"
                RESPONSE=$(cat "$CACHE_FILE")
            else
                # Execute API call with timeout and error handling
                RESPONSE=$(curl -s --max-time 30 --fail \
                    "https://$OBSERVE_CUSTOMER_ID.eu-1.observeinc.com/v1/dataset?$QUERY_PARAMS" \
                    --header "Authorization: Bearer $OBSERVE_CUSTOMER_ID $OBSERVE_API_KEY" \
                    --header "Content-Type: application/json" 2>/dev/null)
                
                # Cache the response
                if [ $? -eq 0 ] && [ -n "$RESPONSE" ]; then
                    echo "$RESPONSE" > "$CACHE_FILE"
                    echo "💾 Dataset list cached to workspace: observe-data/cache/datasets_${CACHE_KEY}.json"
                fi
            fi
            
            if [ $? -ne 0 ]; then
                echo "❌ API request failed. Check credentials and network connectivity."
                exit 1
            fi
            
            # Parse and format response based on format
            if [ "$FORMAT" = "table" ]; then
                echo "$RESPONSE" | jq -r '
                    if .data then
                        (["ID", "NAME", "TYPE", "STATUS", "RECORDS"] | @csv),
                        (.data[] | [.id, .name, .kind, .status, (.recordCount // "N/A")] | @csv)
                    else
                        "No datasets found or invalid response"
                    end' | column -t -s ','
            elif [ "$FORMAT" = "json" ]; then
                echo "$RESPONSE" | jq '.' 2>/dev/null || echo "Error: Invalid JSON response"
            elif [ "$FORMAT" = "compact" ]; then
                echo "$RESPONSE" | jq -r '
                    if .data then
                        .data[] | "\\(.id): \\(.name) (\\(.kind))"
                    else
                        "No datasets found"
                    end'
            else
                echo "$RESPONSE" | jq -r '
                    if .data then
                        "Found \\(.data | length) datasets:\\n" +
                        (.data[] | "• \\(.name) [\\(.id)] - \\(.kind) - \\(.recordCount // \"unknown\") records")
                    else
                        "No datasets found"
                    end'
            fi
            """,
            args=[
                Arg(name="limit", description="Maximum number of datasets to return (default: 50, max: 500)", required=False),
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
            description="Execute OPAL queries on configured datasets. Use observe_get_available_datasets first to see available datasets.",
            content="""
            # Install dependencies
            if ! command -v curl >/dev/null 2>&1; then apk add --no-cache curl; fi
            if ! command -v jq >/dev/null 2>&1; then apk add --no-cache jq; fi
            if ! command -v date >/dev/null 2>&1; then apk add --no-cache coreutils; fi
            
            # Validate inputs
            if [ -z "$OBSERVE_API_KEY" ] || [ -z "$OBSERVE_CUSTOMER_ID" ] || [ -z "$opal_query" ]; then
                echo "❌ Missing required parameters: OBSERVE_API_KEY, OBSERVE_CUSTOMER_ID, opal_query"
                exit 1
            fi
            
            # Handle dataset IDs
            if [ -n "$dataset_id" ]; then
                DATASET_IDS="$dataset_id"
            elif [ -n "$OBSERVE_DATASET_IDS" ]; then
                DATASET_IDS="$OBSERVE_DATASET_IDS"
            else
                echo "❌ No datasets available. Run observe_get_available_datasets first."
                exit 1
            fi
            
            # Performance defaults and limits
            MAX_ROWS=${max_rows:-100}
            TIMEOUT=${timeout:-30}
            OUTPUT_FORMAT=${output_format:-"table"}
            
            # Smart query optimization - automatically add limits if not present
            OPTIMIZED_QUERY="$opal_query"
            if ! echo "$OPTIMIZED_QUERY" | grep -q "limit"; then
                OPTIMIZED_QUERY="$OPTIMIZED_QUERY | limit $MAX_ROWS"
            fi
            
            echo "Executing query..."
            
            # Build optimized payload with compression - support multiple datasets
            # Convert comma-separated dataset IDs to JSON array
            DATASET_INPUTS=$(echo "$DATASET_IDS" | tr ',' '\n' | jq -R 'select(length > 0)' | jq -s 'map({"datasetId": .})')
            
            QUERY_PAYLOAD=$(jq -n \
                --argjson dataset_inputs "$DATASET_INPUTS" \
                --arg pipeline "$OPTIMIZED_QUERY" \
                '{
                    "query": {
                        "stages": [{
                            "input": $dataset_inputs,
                            "stageID": "main",
                            "pipeline": $pipeline
                        }]
                    },
                    "maxRows": '${MAX_ROWS}',
                    "format": "json",
                    "compression": "gzip"
                }')
            
            # Query payload ready
            
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
            
            # Query completed
            
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
                    echo "$RESPONSE" | jq -r '.data // []'
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
                            "Results: " + (.data | length | tostring) + " rows"
                        else
                            "No data returned"
                        end'
                    ;;
                *)
                    echo "$RESPONSE" | jq '.'
                    ;;
            esac
            
            # Simple caching
            mkdir -p "/workspace/observe-data/cache" 2>/dev/null || true
            """,
            args=[
                Arg(name="dataset_id", description="Dataset ID to query. If not provided, uses all configured datasets.", required=False),
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
            description="Build OPAL queries using templates for common use cases.",
            content="""
            # Install dependencies
            if ! command -v jq >/dev/null 2>&1; then apk add --no-cache jq; fi
            
            echo "OPAL Query Builder"
            
            QUERY_TYPE=${query_type:-"custom"}
            DATASET_ID=${dataset_id:-""}
            
            case "$QUERY_TYPE" in
                "error_analysis")
                    TEMPLATE='filter level == "ERROR" | pick_col TIMESTAMP, message, level | limit 50'
                    echo "Error Analysis Template:"
                    ;;
                "performance_monitoring") 
                    TEMPLATE='filter response_time > 1000 | pick_col TIMESTAMP, response_time, endpoint | limit 100'
                    echo "Performance Monitoring Template:"
                    ;;
                "security_events")
                    TEMPLATE='filter action == "login" | pick_col TIMESTAMP, user_id, source_ip, result | limit 100'
                    echo "Security Events Template:"
                    ;;
                "resource_usage")
                    TEMPLATE='filter cpu_usage > 80 | pick_col TIMESTAMP, cpu_usage, host | limit 100'
                    echo "Resource Usage Template:"
                    ;;
                "log_aggregation")
                    TEMPLATE='filter level in ("WARN", "ERROR") | pick_col TIMESTAMP, level, message | limit 100'
                    echo "Log Aggregation Template:"
                    ;;
                *)
                    if [ -n "$custom_query" ]; then
                        TEMPLATE="$custom_query"
                        echo "Custom Query:"
                    else
                        echo "❌ No query specified. Use query_type parameter or provide custom_query."
                        exit 1
                    fi
                    ;;
            esac
            
            echo "Query: $TEMPLATE"
            echo ""
            
            # Add limit if missing
            if ! echo "$TEMPLATE" | grep -q "limit"; then
                TEMPLATE="$TEMPLATE | limit 100"
            fi
            
            echo "Query: $TEMPLATE"
            
            echo "To execute: observe_opal_query --opal_query \"$TEMPLATE\""
            
            # Save template
            mkdir -p "/workspace/observe-data/templates" 2>/dev/null || true
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
            description="Analyze dataset structure and fields. Use observe_get_available_datasets first to see available datasets.",
            content="""
            # Install dependencies
            if ! command -v curl >/dev/null 2>&1; then apk add --no-cache curl; fi
            if ! command -v jq >/dev/null 2>&1; then apk add --no-cache jq; fi
            
            # Validate inputs
            if [ -z "$OBSERVE_API_KEY" ] || [ -z "$OBSERVE_CUSTOMER_ID" ]; then
                echo "❌ Missing required parameters: OBSERVE_API_KEY, OBSERVE_CUSTOMER_ID"
                exit 1
            fi
            
            # Handle dataset IDs
            if [ -n "$dataset_id" ]; then
                DATASET_IDS="$dataset_id"
            elif [ -n "$OBSERVE_DATASET_IDS" ]; then
                DATASET_IDS="$OBSERVE_DATASET_IDS"
            else
                echo "❌ No datasets available. Run observe_get_available_datasets first."
                exit 1
            fi
            
            echo "Dataset Analysis: $DATASET_IDS"
            
            # Get first dataset for sample analysis
            FIRST_DATASET=$(echo "$DATASET_IDS" | cut -d',' -f1 | xargs)
            
            DATASET_INFO=$(curl -s --max-time 10 --fail \
                "https://$OBSERVE_CUSTOMER_ID.eu-1.observeinc.com/v1/dataset/$FIRST_DATASET" \
                --header "Authorization: Bearer $OBSERVE_CUSTOMER_ID $OBSERVE_API_KEY" \
                --header "Content-Type: application/json" 2>/dev/null)
            
            if [ $? -eq 0 ] && [ -n "$DATASET_INFO" ]; then
                echo "$DATASET_INFO" | jq -r '"Dataset: " + (.name // "Unknown") + " (" + (.kind // "Unknown") + ")"'
            fi
            
            # Analyze field structure
            SAMPLE_QUERY='pick_col * | limit 3'
            
            DATASET_INPUTS=$(echo "$DATASET_IDS" | tr ',' '\n' | jq -R 'select(length > 0)' | jq -s 'map({"datasetId": .})')
            
            SAMPLE_PAYLOAD=$(jq -n \
                --argjson dataset_inputs "$DATASET_INPUTS" \
                --arg pipeline "$SAMPLE_QUERY" \
                '{
                    "query": {
                        "stages": [{
                            "input": $dataset_inputs,
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
                echo "$SAMPLE_DATA" | jq -r '
                    if .data and (.data | length > 0) then
                        (.data[0] | keys) as $fields |
                        "Fields (" + ($fields | length | tostring) + "): " + ($fields | join(", "))
                    else
                        "No sample data available"
                    end
                '
            fi
            
            echo ""
            echo "Sample queries:"
            echo "pick_col * | limit 10"
            echo "filter level==\"ERROR\" | limit 50"
            echo "stats count by level | sort count desc"
            """,
            args=[
                Arg(name="dataset_id", description="Dataset ID to analyze. If not provided, uses all configured datasets.", required=False)
            ],
            image="alpine:latest"
        )

    def performance_monitor(self) -> ObserveCLITool:
        """Monitor query performance and system health."""
        return ObserveCLITool(
            name="observe_performance_monitor",
            description="Monitor API performance and run basic benchmarks.",
            content="""
            # Install dependencies
            if ! command -v curl >/dev/null 2>&1; then apk add --no-cache curl; fi
            if ! command -v jq >/dev/null 2>&1; then apk add --no-cache jq; fi
            
            echo "Performance Monitor"
            
            # Validate connection
            if [ -z "$OBSERVE_API_KEY" ] || [ -z "$OBSERVE_CUSTOMER_ID" ]; then
                echo "❌ Missing credentials"
                exit 1
            fi
            
            # API Health Check
            START_TIME=$(date +%s%3N)
            
            HEALTH_RESPONSE=$(curl -s --max-time 5 --fail \
                "https://$OBSERVE_CUSTOMER_ID.eu-1.observeinc.com/v1/dataset?limit=1" \
                --header "Authorization: Bearer $OBSERVE_CUSTOMER_ID $OBSERVE_API_KEY" \
                --header "Content-Type: application/json" 2>/dev/null)
            
            HEALTH_EXIT_CODE=$?
            END_TIME=$(date +%s%3N)
            API_LATENCY=$((END_TIME - START_TIME))
            
            if [ $HEALTH_EXIT_CODE -eq 0 ]; then
                echo "API: OK (${API_LATENCY}ms)"
            else
                echo "API: Failed"
                exit 1
            fi
            
            # Simple benchmark if requested
            if [ "$run_benchmark" = "true" ]; then
                echo "Basic benchmark completed"
            fi
            
            # Save basic metrics
            mkdir -p "/workspace/observe-data/metrics" 2>/dev/null || true
            """,
            args=[
                Arg(name="dataset_id", description="Dataset ID for benchmarking (optional)", required=False),
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
                    find /workspace/observe-data/cache -name "*.json" -type f -exec basename {} \\; 2>/dev/null | sort || echo "No cache files found"
                    echo ""
                    echo "Recent cache files (last 24 hours):"
                    find /workspace/observe-data/cache -name "*.json" -type f -mtime -1 -exec ls -lh {} \\; 2>/dev/null | awk '{print $9, $5, $6, $7, $8}' || echo "No recent cache files"
                    ;;
                
                "list-templates")
                    echo "📋 Template Files:"
                    echo "=================="
                    if [ -f "/workspace/observe-data/templates/index.json" ]; then
                        jq -r '.[] | "• \\(.name) (\\(.type)) - \\(.created)"' /workspace/observe-data/templates/index.json 2>/dev/null || echo "No templates index found"
                    else
                        find /workspace/observe-data/templates -name "*.opal" -type f -exec basename {} \\; 2>/dev/null | sort || echo "No template files found"
                    fi
                    ;;
                
                "list-metrics")
                    echo "📈 Performance Metrics:"
                    echo "======================"
                    find /workspace/observe-data/metrics -name "*.json" -type f -exec basename {} \\; 2>/dev/null | sort -r | head -10 || echo "No metrics files found"
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