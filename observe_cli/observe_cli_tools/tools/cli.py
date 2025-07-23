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

    def execute_opal_query(self) -> ObserveCLITool:
        return ObserveCLITool(
            name="observe_opal_query",
            description=(
                "Execute optimized OPAL queries on Observe datasets. Returns a limited number of recent records from the specified time interval, "
                "optionally filtered by content in any field. Supports field selection for performance optimization with large records. "
                "Automatically uses dataset IDs from DATASET_IDS environment variable and tries both US and EU regional endpoints."
            ),
            content="""
            #!/bin/sh
            set -e
            
            # Validate environment
            if [ -z "$OBSERVE_API_KEY" ] || [ -z "$OBSERVE_CUSTOMER_ID" ] || [ -z "$DATASET_IDS" ]; then
                echo "❌ OBSERVE_API_KEY, OBSERVE_CUSTOMER_ID, and DATASET_IDS are required"
                exit 1
            fi
            
            echo "🔧 Using dataset IDs: $DATASET_IDS"
            
            # Install required tools
            apk add --no-cache jq curl bc >/dev/null 2>&1 || {
                echo "❌ Failed to install jq, curl, and bc"
                exit 1
            }
            
            # Parse arguments
            interval="$interval"
            start_time="$start_time"
            end_time="$end_time"
            filter_term="$filter"
            filter_type="$filter_type"
            fields="$fields"
            limit_count="$limit"
            
            # Default values for performance optimization
            if [ -z "$filter_type" ]; then
                filter_type="body"
            fi
            
            if [ -z "$limit_count" ]; then
                limit_count="25"  # Reduced from 250 for performance with large records
            fi
            
            # Build field selection part of pipeline
            field_selection=""
            if [ -n "$fields" ]; then
                # User specified specific fields
                field_selection="pick_col $fields | "
                echo "📝 Field selection: $fields"
            else
                # Default behavior - include all fields but warn about potential size
                echo "💡 Including all fields (including body with log content)"
                echo "   Note: Some records can be 40k+ characters - using limit=$limit_count for performance"
            fi
            
            # Use jq to properly construct the input array and pipeline from dataset IDs  
            echo "🔧 Building query from dataset IDs: $DATASET_IDS"
            if [ -n "$filter_term" ]; then
                pipeline_str=$(printf '%sfilter %s ~ "%s" | limit %s' "$field_selection" "$filter_type" "$filter_term" "$limit_count")
                echo "📝 OPAL pipeline: $pipeline_str"
                QUERY_JSON=$(echo "$DATASET_IDS" | jq -R -s \
                    --arg filter_pipeline "$pipeline_str" \
                    --arg customer_id "$OBSERVE_CUSTOMER_ID" \
                    'split(",") | map(gsub("^[[:space:]]+|[[:space:]]+$"; "")) | map(select(length > 0)) | 
                    . as $dataset_ids | 
                    if length == 1 then
                        [{
                            inputName: "main",
                            datasetId: ("o::" + $customer_id + ":dataset:" + $dataset_ids[0])
                        }]
                    else
                        map({
                            inputName: ("dataset_" + .),
                            datasetId: ("o::" + $customer_id + ":dataset:" + .)
                        })
                    end as $inputs |
                    {
                        "query": {
                            "stages": [{
                                "input": $inputs,
                                "stageID": "main", 
                                "pipeline": $filter_pipeline
                            }]
                        }
                    }')
            else
                pipeline_str=$(printf '%slimit %s' "$field_selection" "$limit_count")
                echo "📝 OPAL pipeline: $pipeline_str"
                QUERY_JSON=$(echo "$DATASET_IDS" | jq -R -s \
                    --arg customer_id "$OBSERVE_CUSTOMER_ID" \
                    --arg pipeline "$pipeline_str" \
                    'split(",") | map(gsub("^[[:space:]]+|[[:space:]]+$"; "")) | map(select(length > 0)) | 
                    . as $dataset_ids | 
                    if length == 1 then
                        [{
                            inputName: "main",
                            datasetId: ("o::" + $customer_id + ":dataset:" + $dataset_ids[0])
                        }]
                    else
                        map({
                            inputName: ("dataset_" + .),
                            datasetId: ("o::" + $customer_id + ":dataset:" + .)
                        })
                    end as $inputs |
                    {
                        "query": {
                            "stages": [{
                                "input": $inputs,
                                "stageID": "main", 
                                "pipeline": $pipeline
                            }]
                        }
                    }')
            fi
            echo ""
            
            # Performance guidance
            if [ "$limit_count" -gt 50 ]; then
                echo "⚠️  High limit ($limit_count) may cause slow responses with large log records"
                echo "💡 Consider starting with a smaller limit and increasing if needed"
            fi
            
            # Validate that the query was constructed successfully
            if [ -z "$QUERY_JSON" ] || ! echo "$QUERY_JSON" | jq empty 2>/dev/null; then
                echo "❌ Failed to construct query JSON from dataset IDs: $DATASET_IDS"
                exit 1
            fi
            
            # Validate that we have at least one dataset input
            INPUT_COUNT=$(echo "$QUERY_JSON" | jq -r '.query.stages[0].input | length')
            if [ "$INPUT_COUNT" -eq 0 ]; then
                echo "❌ No valid dataset IDs found in dataset IDs: $DATASET_IDS"
                exit 1
            fi
            
            # Build API URL with time parameters
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
            
            echo "🚀 Executing OPAL query..."
            echo ""
            
            # Track query start time for performance monitoring
            START_TIME=$(date +%s)
            
            # Try both regions - one will work, one will fail
            RESPONSE=""
            REGION_USED=""
            
            for REGION in "us-1" "eu-1"; do
                echo "🔍 Trying $REGION region..."
                API_BASE_URL="https://$OBSERVE_CUSTOMER_ID.$REGION.observeinc.com"
                API_URL="$API_BASE_URL/v1/meta/export/query"
                
                if [ -n "$PARAMS" ]; then
                    API_URL="$API_URL?$PARAMS"
                fi
                
                echo "   📡 Full API URL: $API_URL"
                echo "   🔑 Customer ID: $OBSERVE_CUSTOMER_ID"
                echo "   📦 Query payload size: $(echo "$QUERY_JSON" | wc -c) bytes"
                echo "   ⏱️  Starting curl request..."
                
                CURL_START=$(date +%s)
                
                # Debug: show exact command being run
                echo "   🐛 Debug: curl command will be:"
                echo "   curl -s --insecure '$API_URL' --request POST --header 'Authorization: Bearer $OBSERVE_CUSTOMER_ID [HIDDEN]' --header 'Content-Type: application/json' --header 'Accept: application/x-ndjson' --data-raw '[JSON]' --fail"
                
                # Add temporary timeout for debugging
                RESPONSE=$(timeout 10 curl -s \
                    --insecure \
                    "$API_URL" \
                    --request POST \
                    --header "Authorization: Bearer $OBSERVE_CUSTOMER_ID $OBSERVE_API_KEY" \
                    --header "Content-Type: application/json" \
                    --header "Accept: application/x-ndjson" \
                    --data-raw "$QUERY_JSON" \
                    --fail \
                    2>&1)
                    
                CURL_EXIT_CODE=$?
                CURL_END=$(date +%s)
                CURL_DURATION=$((CURL_END - CURL_START))
                
                echo "   ⏱️  Curl completed in ${CURL_DURATION}s (exit code: $CURL_EXIT_CODE)"
                
                if [ $CURL_EXIT_CODE -ne 0 ]; then
                    echo "   ❌ Curl failed with exit code $CURL_EXIT_CODE"
                    case $CURL_EXIT_CODE in
                        28) echo "   💡 Timeout occurred (${CURL_DURATION}s)" ;;
                        6)  echo "   💡 Couldn't resolve host: $API_BASE_URL" ;;
                        7)  echo "   💡 Failed to connect to host: $API_BASE_URL" ;;
                        22) echo "   💡 HTTP error response (404 - wrong region)" ;;
                        52) echo "   💡 Empty reply from server" ;;
                        60) echo "   💡 SSL certificate verification failed" ;;
                        *) echo "   💡 Curl error $CURL_EXIT_CODE" ;;
                    esac
                    echo "   📝 Curl output: $(echo "$RESPONSE" | tail -5)"
                    echo ""
                    continue
                fi
                
                if [ -z "$RESPONSE" ]; then
                    echo "   ✅ Empty response - query executed successfully but found no matching data"
                    echo "   💡 This usually means your filter didn't match any records"
                    REGION_USED="$REGION"
                    RESPONSE='{"data":[],"message":"No data found matching your query criteria"}'
                    echo ""
                    break
                fi
                
                echo "   📏 Response length: $(echo "$RESPONSE" | wc -c) characters"
                
                # Extract just the JSON part (curl -v adds debug info)
                JSON_RESPONSE=$(echo "$RESPONSE" | sed -n '/^{/,$p' | tail -n +1)
                
                if [ -z "$JSON_RESPONSE" ]; then
                    echo "   ❌ No JSON found in response"
                    echo "   📄 Raw response: $(echo "$RESPONSE" | head -5)"
                    echo ""
                    continue
                fi
                
                echo "   🔍 Testing JSON validity..."
                
                if echo "$JSON_RESPONSE" | jq empty >/dev/null 2>&1; then
                    echo "   ✅ Valid JSON response"
                    
                    # Check if it's an error response
                    ERROR_CHECK=$(echo "$JSON_RESPONSE" | jq -r '.error // empty' 2>/dev/null)
                    if [ -n "$ERROR_CHECK" ]; then
                        echo "   ❌ $REGION region returned API error: $ERROR_CHECK"
                        echo ""
                        continue
                    else
                        REGION_USED="$REGION"
                        RESPONSE="$JSON_RESPONSE"
                        echo "   ✅ $REGION region succeeded!"
                        echo ""
                        break
                    fi
                else
                    echo "   ❌ Invalid JSON response"
                    echo "   📄 First 200 chars: $(echo "$JSON_RESPONSE" | head -c 200)..."
                    echo ""
                    continue
                fi
            done
            
            END_TIME=$(date +%s)
            QUERY_DURATION=$((END_TIME - START_TIME))
            
            if [ -z "$REGION_USED" ]; then
                echo "❌ Failed to execute query in both US and EU regions"
                echo "💡 Verify your dataset IDs are correct and you have access to them"
                exit 1
            fi
            
            echo "🌍 Using region: $REGION_USED"
            
            # Process response (same as successful version)
            if echo "$RESPONSE" | jq empty >/dev/null 2>&1; then
                echo "📊 Query Results (completed in ${QUERY_DURATION}s):"
                
                # Calculate and display response size info with error handling
                RESPONSE_SIZE=$(echo "$RESPONSE" | wc -c 2>/dev/null || echo "0")
                RECORD_COUNT=$(echo "$RESPONSE" | jq -r '.data | length // 0' 2>/dev/null || echo "0")
                
                # Simple validation and display without complex arithmetic
                if [ -n "$RECORD_COUNT" ] && [ "$RECORD_COUNT" != "null" ] && [ "$RECORD_COUNT" -gt 0 ] 2>/dev/null; then
                    echo "📏 Response: $RECORD_COUNT records, $RESPONSE_SIZE bytes"
                    
                    # Simple performance insights without division
                    if [ "$RESPONSE_SIZE" -gt 500000 ] 2>/dev/null; then
                        echo "📊 Large response detected - rich log content available for analysis"
                        if [ "$RECORD_COUNT" -gt 10 ] 2>/dev/null; then
                            echo "💡 Consider using smaller --limit for faster initial analysis"
                        fi
                    fi
                else
                    echo "📏 Response received successfully"
                fi
                
                echo "$RESPONSE" | jq .
                
                # Check for errors and provide guidance
                if echo "$RESPONSE" | jq -e '.error // .message' >/dev/null 2>&1; then
                    echo ""
                    echo "⚠️  Query completed with errors - see above for details"
                fi
            else
                echo "📄 Raw response (non-JSON):"
                echo "$RESPONSE"
            fi
            """,
            args=[
                Arg(name="interval", description="Time interval relative to now (e.g., '5m', '15m', '30m', '1h')", required=False),
                Arg(name="start_time", description="Start time as ISO timestamp (inclusive)", required=False),
                Arg(name="end_time", description="End time as ISO timestamp (exclusive)", required=False),
                Arg(name="filter", description="Optional filter term to search for (case-insensitive). Searches in the field specified by filter_type (defaults to 'body'). Examples: 'error', 'freighthub', 'exception'", required=False),
                Arg(name="filter_type", description="Field to search in. Available fields: timestamp, applicationName, type, httpMethod, requestURI, statusCode, body, sleuthTraceId, sleuthSpanId, node, vendorCode, user, company, endpoint, eventId, headers, tenantId, transportationMode, userId. Defaults to 'body' (log content).", required=False),
                Arg(name="fields", description="Comma-separated list of specific fields to return (e.g., 'timestamp,user,statusCode,body'). Use for targeted analysis or performance optimization.", required=False),
                Arg(name="limit", description="Maximum number of records to return (default: 25, reduced for performance with large records)", required=False)
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
            description="Deep analysis of dataset structure, field distribution, performance metrics, and optimization recommendations. Tries both US and EU regional endpoints. Provides insights for better query performance.",
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
            
            # Try both regions to get dataset metadata
            echo "📊 Fetching dataset metadata..."
            DATASET_INFO=""
            REGION_USED=""
            
            for REGION in "us-1" "eu-1"; do
                echo "🔍 Trying $REGION region..."
                API_URL="https://$OBSERVE_CUSTOMER_ID.$REGION.observeinc.com/v1/dataset/$dataset_id"
                echo "   📡 API URL: $API_URL"
                echo "   🔑 Customer ID: $OBSERVE_CUSTOMER_ID"
                echo "   ⏱️  Starting curl request..."
                
                CURL_START=$(date +%s)
                DATASET_INFO=$(curl -s --max-time 30 --fail \
                    "$API_URL" \
                    --header "Authorization: Bearer $OBSERVE_CUSTOMER_ID $OBSERVE_API_KEY" \
                    --header "Content-Type: application/json")
                CURL_EXIT_CODE=$?
                CURL_END=$(date +%s)
                CURL_DURATION=$((CURL_END - CURL_START))
                
                echo "   ⏱️  Curl completed in ${CURL_DURATION}s (exit code: $CURL_EXIT_CODE)"
                
                if [ $CURL_EXIT_CODE -ne 0 ]; then
                    echo "   ❌ Curl failed with exit code $CURL_EXIT_CODE"
                    case $CURL_EXIT_CODE in
                        28) echo "   💡 Timeout occurred" ;;
                        6)  echo "   💡 Couldn't resolve host" ;;
                        7)  echo "   💡 Failed to connect to host" ;;
                        22) echo "   💡 HTTP error response" ;;
                        *) echo "   💡 Unknown curl error" ;;
                    esac
                    continue
                fi
                
                if [ -z "$DATASET_INFO" ]; then
                    echo "   ❌ Empty response"
                    continue
                fi
                
                echo "   📏 Response length: $(echo "$DATASET_INFO" | wc -c) characters"
                echo "   🔍 Testing JSON validity..."
                
                if echo "$DATASET_INFO" | jq empty >/dev/null 2>&1; then
                    echo "   ✅ Valid JSON response"
                    # Check if it's an error response
                    if echo "$DATASET_INFO" | jq -e '.error' >/dev/null 2>&1; then
                        ERROR_MSG=$(echo "$DATASET_INFO" | jq -r '.error // "Unknown error"')
                        echo "   ❌ $REGION region returned error: $ERROR_MSG"
                        continue
                    else
                        REGION_USED="$REGION"
                        echo "   ✅ $REGION region succeeded!"
                        break
                    fi
                else
                    echo "   ❌ Invalid JSON response"
                    echo "   📄 First 200 chars: $(echo "$DATASET_INFO" | head -c 200)..."
                    continue
                fi
            done
            
            if [ -z "$REGION_USED" ]; then
                echo "❌ Failed to fetch dataset metadata from both US and EU regions"
                echo "💡 Verify dataset ID exists and you have access to it"
                exit 1
            fi
            
            echo "🌍 Using region: $REGION_USED"
            echo ""
            
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
                "https://$OBSERVE_CUSTOMER_ID.$REGION_USED.observeinc.com/v1/meta/export/query" \
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
            description="Monitor Observe API performance, track query execution times, and provide system health insights. Tries both US and EU regional endpoints. Includes performance benchmarking and optimization tracking.",
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
            
            # Try both regions for API health check
            echo ""
            echo "🏥 API Health Check:"
            START_TIME=$(date +%s%3N)
            
            HEALTH_RESPONSE=""
            REGION_USED=""
            
            for REGION in "us-1" "eu-1"; do
                echo "🔍 Trying $REGION region..."
                API_URL="https://$OBSERVE_CUSTOMER_ID.$REGION.observeinc.com/v1/dataset?limit=1"
                echo "   📡 API URL: $API_URL"
                echo "   🔑 Customer ID: $OBSERVE_CUSTOMER_ID"
                echo "   ⏱️  Starting curl request..."
                
                CURL_START=$(date +%s)
                HEALTH_RESPONSE=$(curl -s --max-time 10 --fail \
                    "$API_URL" \
                    --header "Authorization: Bearer $OBSERVE_CUSTOMER_ID $OBSERVE_API_KEY" \
                    --header "Content-Type: application/json")
                CURL_EXIT_CODE=$?
                CURL_END=$(date +%s)
                CURL_DURATION=$((CURL_END - CURL_START))
                
                echo "   ⏱️  Curl completed in ${CURL_DURATION}s (exit code: $CURL_EXIT_CODE)"
                
                if [ $CURL_EXIT_CODE -ne 0 ]; then
                    echo "   ❌ Curl failed with exit code $CURL_EXIT_CODE"
                    case $CURL_EXIT_CODE in
                        28) echo "   💡 Timeout occurred" ;;
                        6)  echo "   💡 Couldn't resolve host" ;;
                        7)  echo "   💡 Failed to connect to host" ;;
                        22) echo "   💡 HTTP error response" ;;
                        *) echo "   💡 Unknown curl error" ;;
                    esac
                    continue
                fi
                
                if [ -z "$HEALTH_RESPONSE" ]; then
                    echo "   ❌ Empty response"
                    continue
                fi
                
                echo "   📏 Response length: $(echo "$HEALTH_RESPONSE" | wc -c) characters"
                echo "   🔍 Testing JSON validity..."
                
                if echo "$HEALTH_RESPONSE" | jq empty >/dev/null 2>&1; then
                    echo "   ✅ Valid JSON response"
                    # Check if it's an error response
                    if echo "$HEALTH_RESPONSE" | jq -e '.error' >/dev/null 2>&1; then
                        ERROR_MSG=$(echo "$HEALTH_RESPONSE" | jq -r '.error // "Unknown error"')
                        echo "   ❌ $REGION region returned error: $ERROR_MSG"
                        continue
                    else
                        REGION_USED="$REGION"
                        echo "   ✅ $REGION region succeeded!"
                        break
                    fi
                else
                    echo "   ❌ Invalid JSON response"
                    echo "   📄 First 200 chars: $(echo "$HEALTH_RESPONSE" | head -c 200)..."
                    continue
                fi
            done
            
            END_TIME=$(date +%s%3N)
            API_LATENCY=$((END_TIME - START_TIME))
            
            if [ -z "$REGION_USED" ]; then
                echo "❌ Failed to check API health in both US and EU regions"
                echo "💡 Verify your credentials and network connectivity"
                exit 1
            fi
            
            echo "🌍 Using region: $REGION_USED"
            echo "✅ API Status: Healthy"
            echo "⚡ Response Time: ${API_LATENCY}ms"
            
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
                            "https://$OBSERVE_CUSTOMER_ID.$REGION_USED.observeinc.com/v1/meta/export/query" \
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
                    --arg api_status "0" \
                    --arg region "$REGION_USED" \
                    '{
                        "timestamp": $timestamp,
                        "api_latency_ms": ($api_latency | tonumber),
                        "api_healthy": ($api_status == "0"),
                        "customer_id": "'$OBSERVE_CUSTOMER_ID'",
                        "region": $region
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