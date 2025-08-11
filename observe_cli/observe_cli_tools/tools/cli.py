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

    def execute_opal_query(self) -> ObserveCLITool:
        return ObserveCLITool(
            name="observe_opal_query",
            description=(
                "Execute OPAL queries on Observe datasets with flexible filtering. Returns newest records first. "
                "Supports simple and advanced filtering, field selection, and tries both US/EU endpoints.\n\n"
                "SORTING: Always returns newest records first. When limit=10 and 50 results match, you get the 10 MOST RECENT records.\n\n"
                "EXAMPLES:\n"
                "• Recent 500 errors: filter='500'\n"
                "• App errors: filter='filter applicationName ~ \"my-service\" | filter level ~ \"ERROR\"'\n"
                "• Latest timeouts: filter='timeout' with interval='1h'\n\n"
                "FIELDS: timestamp, applicationName, level, loggerName, host, message, sleuthSpanId, sleuthTraceId, tags, FIELDS. "
                "HTTP status codes are in 'message' field content."
            ),
            content="""
            #!/bin/sh
            
            # Validate environment
            if [ -z "$OBSERVE_API_KEYS" ] || [ -z "$OBSERVE_CUSTOMER_ID" ] || [ -z "$DATASET_IDS" ]; then
                echo "❌ OBSERVE_API_KEYS, OBSERVE_CUSTOMER_ID, and DATASET_IDS are required"
                exit 0
            fi
            
            echo "🔧 Using dataset IDs: $DATASET_IDS"
            sleep 1
            
            # Install required tools
            apk add --no-cache jq curl bc >/dev/null 2>&1 || {
                echo "❌ Failed to install jq, curl, and bc"
                exit 0
            }
            
            # Parse API keys from JSON
            NA_API_KEY=$(echo "$OBSERVE_API_KEYS" | jq -r '.NA // empty')
            EU_API_KEY=$(echo "$OBSERVE_API_KEYS" | jq -r '.EU // empty')
            
            if [ -z "$NA_API_KEY" ] || [ -z "$EU_API_KEY" ]; then
                echo "❌ OBSERVE_API_KEYS must contain both 'NA' and 'EU' keys"
                echo "Expected format: {\"NA\": \"key1\", \"EU\": \"key2\"}"
                exit 0
            fi
            
            # Parse arguments
            interval="$interval"
            start_time="$start_time"
            end_time="$end_time"
            filter_term="$filter"
            fields="$fields"

            # Clean up limit parameter by removing any control characters and whitespace
            limit_count=$(echo "$limit" | tr -d '[:cntrl:]' | tr -d '[:space:]')
            
            # Default values for performance optimization
            # Simple filters always search in 'message' field by default
            filter_type="message"
            
            if [ -z "$limit_count" ] || ! echo "$limit_count" | grep -qE '^[0-9]+$'; then
                limit_count="25"
            fi
            
            # Enforce maximum limit of 25 for performance and stability
            if [ "$limit_count" -gt 25 ]; then
                echo "⚠️  Requested limit ($limit_count) exceeds maximum allowed (25). Using limit=25"
                limit_count="25"
            fi
            
            # Build field selection part of pipeline
            field_selection=""
            if [ -n "$fields" ]; then
                # User specified specific fields - will be added AFTER filtering
                field_selection="pick_col $fields"
                echo "📝 Field selection: $fields (applied after filtering)"
            else
                # Default behavior - include all fields but warn about potential size
                echo "💡 Including all fields (including message with log content)"
                echo "   Note: Some records can be 40k+ characters - using limit=$limit_count for performance"
                sleep 1
            fi
            
            # Enhanced filter handling - support both simple and complex OPAL pipeline segments
            filter_pipeline=""
            if [ -n "$filter_term" ]; then
                # Check if the filter contains pipe characters or looks like a complex OPAL pipeline
                if echo "$filter_term" | grep -q '|' || echo "$filter_term" | grep -qE 'filter\s+\w+\s*~' || echo "$filter_term" | grep -qE '\b(stats|sort|top|bottom|pick_col)\b'; then
                    # Advanced/complex filter - use as-is
                    echo "🔧 Using advanced filter pipeline: $filter_term"
                    filter_pipeline="$filter_term"
                    # Add limit if not already present in the pipeline
                    if ! echo "$filter_pipeline" | grep -q 'limit'; then
                        filter_pipeline="$filter_pipeline | limit $limit_count"
                    fi
                else
                    # Simple filter - build traditional single filter
                    echo "🔧 Using simple filter: $filter_type ~ \"$filter_term\""
                    filter_pipeline="filter $filter_type ~ \"$filter_term\""
                fi
            else
                # No filter, start with empty pipeline
                filter_pipeline=""
            fi
            
            # Sorting handled via presentation.orderColumns for newest first
            echo "🔧 Sorting: newest records first via presentation layer"
            
            # Combine filter pipeline with field selection and limit
            # Order: filter operations first, then field selection, then limit
            pipeline_parts=""
            
            # Add filter part if exists
            if [ -n "$filter_pipeline" ]; then
                pipeline_parts="$filter_pipeline"
            fi
            
            # Add field selection if specified
            if [ -n "$field_selection" ]; then
                if [ -n "$pipeline_parts" ]; then
                    pipeline_parts="$pipeline_parts | $field_selection"
                else
                    pipeline_parts="$field_selection"
                fi
            fi
            
            # Add limit at the end (unless already present)
            if echo "$pipeline_parts" | grep -q 'limit'; then
                pipeline_str="$pipeline_parts"
            else
                if [ -n "$pipeline_parts" ]; then
                    pipeline_str="$pipeline_parts | limit $limit_count"
                else
                    pipeline_str="limit $limit_count"
                fi
            fi
            
            # Use jq to properly construct the input array and pipeline from dataset IDs  
            echo "🔧 Building query from dataset IDs: $DATASET_IDS"
            echo "📝 Final OPAL pipeline: $pipeline_str"
            echo ""
            sleep 1
            
            QUERY_JSON=$(echo "$DATASET_IDS" | jq -R -s \
                --arg pipeline "$pipeline_str" \
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
                            "pipeline": $pipeline
                        }]
                    },
                    "presentation": {
                        "orderColumns": [{
                            "columnName": "timestamp",
                            "ascending": false
                        }]
                    }
                }')
            
            # Echo the full OPAL query JSON for debugging and transparency
            echo "📋 Full OPAL Query JSON:"
            echo "$QUERY_JSON" | jq .
            echo ""
            
            # Performance guidance
            if [ "$limit_count" -gt 1000 ]; then
                echo "⚠️  High limit ($limit_count) may cause slow responses with large log records"
                echo "💡 Consider starting with a smaller limit and increasing if needed"
            fi
            
            # Validate that the query was constructed successfully
            if [ -z "$QUERY_JSON" ] || ! echo "$QUERY_JSON" | jq empty 2>/dev/null; then
                echo "❌ Failed to construct query JSON from dataset IDs: $DATASET_IDS"
                exit 0
            fi
            
            # Validate that we have at least one dataset input
            INPUT_COUNT=$(echo "$QUERY_JSON" | jq -r '.query.stages[0].input | length')
            if [ "$INPUT_COUNT" -eq 0 ]; then
                echo "❌ No valid dataset IDs found in dataset IDs: $DATASET_IDS"
                exit 0
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
            sleep 1
            
            # Track query start time for performance monitoring
            START_TIME=$(date +%s)
            
            # Try both regions - one will work, one will fail
            RESPONSE=""
            REGION_USED=""
            
            for REGION in "us-1" "eu-1"; do
                echo "🔍 Trying $REGION region..."
                sleep 1
                
                # Set API key and base URL based on region
                if [ "$REGION" = "us-1" ]; then
                    API_BASE_URL="https://$OBSERVE_CUSTOMER_ID.observeinc.com"
                    CURRENT_API_KEY="$NA_API_KEY"
                    REGION_DISPLAY="US/NA"
                else
                    API_BASE_URL="https://$OBSERVE_CUSTOMER_ID.eu-1.observeinc.com"
                    CURRENT_API_KEY="$EU_API_KEY"
                    REGION_DISPLAY="EU"
                fi
                
                API_URL="$API_BASE_URL/v1/meta/export/query"
                
                if [ -n "$PARAMS" ]; then
                    API_URL="$API_URL?$PARAMS"
                fi
                
                echo "   📡 Full API URL: $API_URL"
                echo "   🔑 Customer ID: $OBSERVE_CUSTOMER_ID"  
                echo "   🌍 Region: $REGION_DISPLAY"
                echo "   📦 Query payload size: $(echo "$QUERY_JSON" | wc -c) bytes"
                echo "   ⏱️  Starting curl request..."
                sleep 1
                
                CURL_START=$(date +%s)
                
                # Use a more robust approach with curl's --write-out for HTTP status
                # and capture both stdout and stderr
                RESPONSE_WITH_STATUS=$(curl -s \
                    --insecure \
                    "$API_URL" \
                    --request POST \
                    --header "Authorization: Bearer $OBSERVE_CUSTOMER_ID $CURRENT_API_KEY" \
                    --header "Content-Type: application/json" \
                    --header "Accept: application/x-ndjson" \
                    --data-raw "$QUERY_JSON" \
                    --write-out "\nHTTPSTATUS:%{http_code}" 2>&1)
                    
                CURL_EXIT_CODE=$?
                CURL_END=$(date +%s)
                CURL_DURATION=$((CURL_END - CURL_START))
                
                echo "   ⏱️  Curl completed in ${CURL_DURATION}s (exit code: $CURL_EXIT_CODE)"
                sleep 1
                
                # Extract HTTP status code and response body
                HTTP_STATUS=$(echo "$RESPONSE_WITH_STATUS" | grep "HTTPSTATUS:" | cut -d: -f2)
                RESPONSE_BODY=$(echo "$RESPONSE_WITH_STATUS" | sed '/HTTPSTATUS:/d')
                

                
                # Handle curl failures (network issues, etc.)
                if [ $CURL_EXIT_CODE -ne 0 ] && [ -z "$HTTP_STATUS" ]; then
                    echo "   ❌ Curl failed with exit code $CURL_EXIT_CODE"
                    case $CURL_EXIT_CODE in
                        28) echo "   💡 Timeout occurred (${CURL_DURATION}s)" ;;
                        6)  echo "   💡 Couldn't resolve host: $API_BASE_URL" ;;
                        7)  echo "   💡 Failed to connect to host: $API_BASE_URL" ;;
                        52) echo "   💡 Empty reply from server" ;;
                        60) echo "   💡 SSL certificate verification failed" ;;
                        *) echo "   💡 Curl error $CURL_EXIT_CODE" ;;
                    esac
                    echo ""
                    sleep 1
                    continue
                fi
                
                # Check HTTP status code for API errors
                if [ -n "$HTTP_STATUS" ] && [ "$HTTP_STATUS" -ge 400 ] 2>/dev/null; then
                    echo "   ❌ HTTP $HTTP_STATUS error from API"
                    if [ -n "$RESPONSE_BODY" ]; then
                        echo "   📝 API Error Response:"
                        # Try to format JSON if possible, otherwise show raw
                        if echo "$RESPONSE_BODY" | jq empty >/dev/null 2>&1; then
                            echo "$RESPONSE_BODY" | jq -r '.message // .error // .' 2>/dev/null || echo "$RESPONSE_BODY"
                        else
                            echo "$RESPONSE_BODY"
                        fi
                    else
                        echo "   📝 No response body received"
                    fi
                    if [ "$HTTP_STATUS" = "404" ]; then
                        echo "   💡 404 likely means wrong region - trying next region"
                    fi
                    echo ""
                    sleep 1
                    continue
                fi
                
                if [ -z "$RESPONSE_BODY" ]; then
                    echo "   ✅ Empty response - query executed successfully but found no matching data"
                    echo "   💡 This usually means your filter didn't match any records"
                    REGION_USED="$REGION"
                    RESPONSE_BODY='{"data":[],"message":"No data found matching your query criteria"}'
                    echo ""
                    sleep 1
                    break
                fi
                
                echo "   📏 Response length: $(echo "$RESPONSE_BODY" | wc -c) characters"
                
                # Use response body directly as JSON
                JSON_RESPONSE="$RESPONSE_BODY"
                
                if [ -z "$JSON_RESPONSE" ]; then
                    echo "   ❌ No JSON found in response"
                    echo "   📄 Raw response: $(echo "$RESPONSE_BODY" | head -5)"
                    echo ""
                    sleep 1
                    continue
                fi
                
                echo "   🔍 Testing JSON validity..."
                sleep 1
                
                if echo "$JSON_RESPONSE" | jq empty >/dev/null 2>&1; then
                    echo "   ✅ Valid JSON response"
                    
                    # Check if it's an error response
                    ERROR_CHECK=$(echo "$JSON_RESPONSE" | jq -r '.error // empty' 2>/dev/null)
                    if [ -n "$ERROR_CHECK" ]; then
                        echo "   ❌ $REGION region returned API error: $ERROR_CHECK"
                        echo ""
                        sleep 1
                        continue
                    else
                        REGION_USED="$REGION"
                        RESPONSE="$JSON_RESPONSE"
                        echo "   ✅ $REGION region succeeded!"
                        echo ""
                        sleep 1
                        break
                    fi
                else
                    echo "   ❌ Invalid JSON response"
                    echo "   📄 First 200 chars: $(echo "$JSON_RESPONSE" | head -c 200)..."
                    echo ""
                    sleep 1
                    continue
                fi
            done
            
            END_TIME=$(date +%s)
            QUERY_DURATION=$((END_TIME - START_TIME))
            
            if [ -z "$REGION_USED" ]; then
                echo "❌ Failed to execute query in both US and EU regions"
                echo "💡 Verify your dataset IDs are correct and you have access to them"
                sleep 1
                exit 0
            fi
            
            echo "🌍 Using region: $REGION_USED"
            sleep 1
            
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
                Arg(name="filter", description="Filter specification. SIMPLE MODE: Use single term (e.g., '500', 'error') - searches in 'message' field by default. ADVANCED MODE: Use complete OPAL filter starting with 'filter'. SYNTAX RULES: Use lowercase 'and'/'or', quote all values, complete boolean expressions. EXAMPLES: Single error: '500' (searches message field). Multiple errors: 'filter message ~ \"500\" or message ~ \"501\" or message ~ \"502\"' (advanced). Complex: 'filter level ~ \"ERROR\" and (message ~ \"500\" or message ~ \"502\")' (advanced). 5xx errors: 'filter message ~ \"500\" or message ~ \"501\" or message ~ \"502\" or message ~ \"503\" or message ~ \"504\" or message ~ \"505\"'. FIELDS: timestamp, applicationName, level, loggerName, host, message, sleuthSpanId, sleuthTraceId, tags, FIELDS.", required=False),

                Arg(name="fields", description="Comma-separated list of specific fields to return (e.g., 'timestamp,applicationName,level,message'). Applied AFTER filtering, so you can filter on fields not included in this list. Use for performance optimization with large records. WARNING: Field names must be exact matches or the query will fail. Available fields: timestamp, applicationName, level, loggerName, host, message, sleuthSpanId, sleuthTraceId, tags, FIELDS. Leave empty to get all fields (safer but slower).", required=False),
                Arg(name="limit", description="Maximum number of records to return (default: 25, balanced for performance and data volume). Ignored if limit is already specified in advanced filter format.", required=False)
            ],
            image="alpine:latest"
        )

CLITools()