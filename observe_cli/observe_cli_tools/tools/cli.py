from typing import List
import sys
from .base import ObserveCLITool, Arg
from kubiya_sdk.tools.registry import tool_registry

class CLITools:
    """Observe API wrapper tools using curl instead of CLI."""

    def __init__(self):
        """Initialize and register all Observe API wrapper tools."""
        try:
            tools = [
                self.run_api_command()
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

    def run_api_command(self) -> ObserveCLITool:
        """Execute any Observe API operation with dynamic parameters."""
        return ObserveCLITool(
            name="observe_api_command",
            description="""
Execute any Observe API operation with dynamic parameters and proper response parsing. 

- Only supported API endpoints/methods are allowed (validated against the Observe OpenAPI spec).
- If you use an invalid endpoint or method, you'll get a clear error and a hint on the correct one.
- Large responses are truncated (100 lines or 10,000 characters max) for usability. Use filters or pagination for more data.
- For custom API calls, use: api <METHOD> <ENDPOINT> [query-params] [body]
""",
            content="""
            # Set up authentication and validation
            if [ -z "$OBSERVE_API_KEY" ]; then
                echo "Error: OBSERVE_API_KEY environment variable is required"
                exit 1
            fi
            
            if [ -z "$OBSERVE_CUSTOMER_ID" ]; then
                echo "Error: OBSERVE_CUSTOMER_ID environment variable is required"
                exit 1
            fi
            
            # Install curl if not available
            if ! command -v curl >/dev/null 2>&1; then
                echo "Installing curl..."
                apk add --no-cache curl
            fi
            
            # Set base URL with correct format
            OBSERVE_BASE_URL="https://$OBSERVE_CUSTOMER_ID.observeinc.com"
            
            # Set default headers with correct Bearer token format
            HEADERS="-H 'Authorization: Bearer $OBSERVE_CUSTOMER_ID $OBSERVE_API_KEY' -H 'Content-Type: application/json'"
            
            # Helper function to build query parameters
            build_query_params() {
                local params=""
                
                # Time range parameters
                if [ -n "$time_start" ]; then
                    params="${params}time-start=$time_start&"
                fi
                if [ -n "$time_end" ]; then
                    params="${params}time-end=$time_end&"
                fi
                if [ -n "$time_preset" ]; then
                    params="${params}time-preset=$time_preset&"
                fi
                
                # Filter parameters
                if [ -n "$filter" ]; then
                    params="${params}filter=$filter&"
                fi
                if [ -n "$filter_column" ] && [ -n "$filter_value" ]; then
                    if [ -n "$filter_operator" ]; then
                        params="${params}filter=$filter_column|$filter_operator|$filter_value&"
                    else
                        params="${params}filter-$filter_column=$filter_value&"
                    fi
                fi
                
                # OPAL parameter
                if [ -n "$opal" ]; then
                    params="${params}opal=$opal&"
                fi
                
                # Parameter parameters
                if [ -n "$param_key" ] && [ -n "$param_value" ]; then
                    params="${params}param-$param_key=$param_value&"
                fi
                
                # Tab parameter
                if [ -n "$v_tab" ]; then
                    params="${params}v-tab=$v_tab&"
                fi
                
                # Dashboard parameter
                if [ -n "$v_dash" ]; then
                    params="${params}v-dash=$v_dash&"
                fi
                
                # Remove trailing & if present
                params=$(echo "$params" | sed 's/&$//')
                echo "$params"
            }
            
            # Helper function to execute curl with proper output formatting
            execute_curl() {
                local method="$1"
                local url="$2"
                local data="$3"
                
                # Execute curl with metadata and response body separated by a unique delimiter
                if [ -n "$data" ]; then
                    curl -s -w "METADATA_START\nHTTP_STATUS:%{http_code}\nRESPONSE_TIME:%{time_total}s\nMETADATA_END\n" \
                         -X "$method" \
                         $HEADERS \
                         -d "$data" \
                         "$url"
                else
                    curl -s -w "METADATA_START\nHTTP_STATUS:%{http_code}\nRESPONSE_TIME:%{time_total}s\nMETADATA_END\n" \
                         $HEADERS \
                         "$url"
                fi
            }
            
            # Static list of valid endpoints and methods (from OpenAPI spec)
            VALID_ENDPOINTS="/v1/login POST /v1/login/delegated POST /v1/login/delegated/{serverToken} GET /v1/meta/export/query POST /v1/meta/export/query/page GET /v1/meta/export/worksheet/{worksheetId} POST /v1/meta/reftable GET /v1/meta/reftable POST /v1/meta/reftable/{id} GET /v1/meta/reftable/{id} PUT /v1/meta/reftable/{id} DELETE /v1/dataset GET /v1/dataset/{id} GET /v1/monitors GET /v1/monitors POST /v1/monitors/{id} GET /v1/monitors/{id} PATCH /v1/monitors/{id} DELETE /v1/monitor-mute-rules GET /v1/monitor-mute-rules POST /v1/monitor-mute-rules/{id} GET /v1/monitor-mute-rules/{id} DELETE /v1/referencetables GET /v1/referencetables POST /v1/referencetables/{id} GET /v1/referencetables/{id} PATCH /v1/referencetables/{id} DELETE /v1/referencetables/{id} PUT"

            # Helper to print valid endpoints/methods
            print_valid_endpoints() {
                echo "\nSupported API endpoints and methods (from Observe OpenAPI):"
                echo "$VALID_ENDPOINTS" | tr ' ' '\n' | paste - -
            }

            # Helper to check if endpoint/method is valid
            is_valid_api() {
                local method="$1"
                local endpoint="$2"
                # Remove query params for validation
                endpoint="$(echo "$endpoint" | cut -d'?' -f1)"
                # Replace numeric path params with {id} for matching
                endpoint="$(echo "$endpoint" | sed -E 's/[0-9]+|[a-f0-9\-]{8,}/{id}/g')"
                # Check for match
                if echo "$VALID_ENDPOINTS" | grep -q "${endpoint} ${method}"; then
                    return 0
                else
                    return 1
                fi
            }
            
            # Parse the command to determine operation type
            if [ -z "$command" ]; then
                echo "Error: Command is required"
                echo "Usage examples:"
                echo "  'dataset list' - List all datasets"
                echo "  'dataset show <dataset-id>' - Show dataset details"
                echo "  'monitors list' - List all monitors"
                echo "  'monitors show <monitor-id>' - Show monitor details"
                echo "  'monitor-mute-rules list' - List all monitor mute rules"
                echo "  'monitor-mute-rules show <mute-rule-id>' - Show monitor mute rule details"
                echo "  'referencetables list' - List all reference tables"
                echo "  'referencetables show <table-id>' - Show reference table details"
                echo "  'query <dataset-id> <opal-query>' - Execute OPAL query"
                echo "  'api <method> <endpoint> [query-params] [body]' - Custom API call"
                echo "  'advanced-query <dataset-id> [options]' - Advanced query with filters and parameters"
                echo ""
                echo "Advanced URL Parameters:"
                echo "  Time ranges: startTime, endTime, interval"
                echo "  Filters: filter-<column>=<value>, filter=<column>|<operator>|<value>"
                echo "  OPAL: opal=<opal-statement>"
                echo "  Parameters: param-<key>=<value>"
                echo ""
                echo "Advanced Query Examples:"
                echo "  advanced-query 41007104 --interval 1h"
                echo "  advanced-query 41007104 --startTime 2023-04-20T16:20:00Z --endTime 2023-04-20T16:30:00Z"
                echo "  advanced-query 41007104 --opal 'filter severity == \"error\"'"
                exit 1
            fi
            
            # Split command into parts
            set -- $command
            OPERATION="$1"
            SUB_OPERATION="$2"
            
            echo "=== Observe API Operation ==="
            echo "Command: $command"
            echo "Operation: $OPERATION"
            echo "Sub-operation: $SUB_OPERATION"
            echo "Base URL: $OBSERVE_BASE_URL"
            echo ""
            
            # Handle different operation types
            case "$OPERATION" in
                "dataset")
                    case "$SUB_OPERATION" in
                        "list")
                            echo "Listing datasets..."
                            echo "DEBUG: Executing GET request to $OBSERVE_BASE_URL/v1/dataset"
                            response=$(execute_curl "GET" "$OBSERVE_BASE_URL/v1/dataset")
                            ;;
                        "show")
                            if [ -z "$3" ]; then
                                echo "Error: Dataset ID is required for 'dataset show'"
                                exit 1
                            fi
                            dataset_id="$3"
                            echo "Showing dataset: $dataset_id"
                            echo "DEBUG: Executing GET request to $OBSERVE_BASE_URL/v1/dataset/$dataset_id"
                            response=$(execute_curl "GET" "$OBSERVE_BASE_URL/v1/dataset/$dataset_id")
                            ;;
                        *)
                            echo "Error: Unknown dataset operation: $SUB_OPERATION"
                            echo "Supported: list, show"
                            exit 1
                            ;;
                    esac
                    ;;
                "monitors")
                    case "$SUB_OPERATION" in
                        "list")
                            echo "Listing monitors..."
                            echo "DEBUG: Executing GET request to $OBSERVE_BASE_URL/v1/monitors"
                            response=$(execute_curl "GET" "$OBSERVE_BASE_URL/v1/monitors")
                            ;;
                        "show")
                            if [ -z "$3" ]; then
                                echo "Error: Monitor ID is required for 'monitors show'"
                                exit 1
                            fi
                            monitor_id="$3"
                            echo "Showing monitor: $monitor_id"
                            echo "DEBUG: Executing GET request to $OBSERVE_BASE_URL/v1/monitors/$monitor_id"
                            response=$(execute_curl "GET" "$OBSERVE_BASE_URL/v1/monitors/$monitor_id")
                            ;;
                        *)
                            echo "Error: Unknown monitors operation: $SUB_OPERATION"
                            echo "Supported: list, show"
                            exit 1
                            ;;
                    esac
                    ;;
                "monitor-mute-rules")
                    case "$SUB_OPERATION" in
                        "list")
                            echo "Listing monitor mute rules..."
                            echo "DEBUG: Executing GET request to $OBSERVE_BASE_URL/v1/monitor-mute-rules"
                            response=$(execute_curl "GET" "$OBSERVE_BASE_URL/v1/monitor-mute-rules")
                            ;;
                        "show")
                            if [ -z "$3" ]; then
                                echo "Error: Mute Rule ID is required for 'monitor-mute-rules show'"
                                exit 1
                            fi
                            mute_rule_id="$3"
                            echo "Showing monitor mute rule: $mute_rule_id"
                            echo "DEBUG: Executing GET request to $OBSERVE_BASE_URL/v1/monitor-mute-rules/$mute_rule_id"
                            response=$(execute_curl "GET" "$OBSERVE_BASE_URL/v1/monitor-mute-rules/$mute_rule_id")
                            ;;
                        *)
                            echo "Error: Unknown monitor-mute-rules operation: $SUB_OPERATION"
                            echo "Supported: list, show"
                            exit 1
                            ;;
                    esac
                    ;;
                "referencetables")
                    case "$SUB_OPERATION" in
                        "list")
                            echo "Listing reference tables..."
                            echo "DEBUG: Executing GET request to $OBSERVE_BASE_URL/v1/referencetables"
                            response=$(execute_curl "GET" "$OBSERVE_BASE_URL/v1/referencetables")
                            ;;
                        "show")
                            if [ -z "$3" ]; then
                                echo "Error: Reference Table ID is required for 'referencetables show'"
                                exit 1
                            fi
                            table_id="$3"
                            echo "Showing reference table: $table_id"
                            echo "DEBUG: Executing GET request to $OBSERVE_BASE_URL/v1/referencetables/$table_id"
                            response=$(execute_curl "GET" "$OBSERVE_BASE_URL/v1/referencetables/$table_id")
                            ;;
                        *)
                            echo "Error: Unknown referencetables operation: $SUB_OPERATION"
                            echo "Supported: list, show"
                            exit 1
                            ;;
                    esac
                    ;;
                "query")
                    if [ -z "$2" ] || [ -z "$3" ]; then
                        echo "Error: Query requires dataset ID and OPAL query"
                        echo "Usage: query <dataset-id> <opal-query>"
                        exit 1
                    fi
                    dataset_id="$2"
                    shift 2
                    opal_query="$*"
                    echo "Executing OPAL query on dataset: $dataset_id"
                    echo "Query: $opal_query"
                    # Prepare OPAL query payload
                    QUERY_PAYLOAD='{"query": {"stages": [{"input": [{"datasetId": "'$dataset_id'"}], "stageID": "main", "pipeline": "'$opal_query'"}]}}'
                    echo "DEBUG: Executing POST request to $OBSERVE_BASE_URL/v1/meta/export/query"
                    response=$(execute_curl "POST" "$OBSERVE_BASE_URL/v1/meta/export/query" "$QUERY_PAYLOAD")
                    ;;
                "advanced-query")
                    if [ -z "$2" ]; then
                        echo "Error: Advanced query requires dataset ID"
                        echo "Usage: advanced-query <dataset-id> [options]"
                        echo ""
                        echo "Options:"
                        echo "  --startTime <ISO8601>         Start time (e.g. 2023-04-20T16:20:00Z)"
                        echo "  --endTime <ISO8601>           End time (e.g. 2023-04-20T16:30:00Z)"
                        echo "  --interval <duration>         Interval (e.g. 1h, 10m)"
                        echo "  --opal <opal-statement>       OPAL statement"
                        echo ""
                        echo "Examples:"
                        echo "  advanced-query 41007104 --interval 1h"
                        echo "  advanced-query 41007104 --startTime 2023-04-20T16:20:00Z --endTime 2023-04-20T16:30:00Z"
                        echo "  advanced-query 41007104 --opal 'filter severity == \"error\"'"
                        exit 1
                    fi
                    dataset_id="$2"
                    shift 2
                    # Parse advanced options
                    while [ $# -gt 0 ]; do
                        case "$1" in
                            --startTime)
                                startTime="$2"
                                shift 2
                                ;;
                            --endTime)
                                endTime="$2"
                                shift 2
                                ;;
                            --interval)
                                interval="$2"
                                shift 2
                                ;;
                            --opal)
                                opal="$2"
                                shift 2
                                ;;
                            *)
                                echo "Error: Unknown option $1"
                                exit 1
                                ;;
                        esac
                    done
                    # Build query payload
                    QUERY_PAYLOAD="{\"query\": {\"stages\": [{\"input\": [{\"datasetId\": \"$dataset_id\"}], \"stageID\": \"main\", \"pipeline\": \"$opal\"}]}}"
                    # Build query params
                    query_params=""
                    [ -n "$startTime" ] && query_params="${query_params}startTime=$startTime&"
                    [ -n "$endTime" ] && query_params="${query_params}endTime=$endTime&"
                    [ -n "$interval" ] && query_params="${query_params}interval=$interval&"
                    query_params=$(echo "$query_params" | sed 's/&$//')
                    full_url="$OBSERVE_BASE_URL/v1/meta/export/query"
                    [ -n "$query_params" ] && full_url="$full_url?$query_params"
                    echo "DEBUG: Executing POST request to $full_url"
                    response=$(execute_curl "POST" "$full_url" "$QUERY_PAYLOAD")
                    ;;
                "api")
                    if [ -z "$2" ] || [ -z "$3" ]; then
                        echo "Error: API call requires method and endpoint"
                        echo "Usage: api <method> <endpoint> [query-params] [body]"
                        print_valid_endpoints
                        exit 1
                    fi
                    method="$2"
                    endpoint="$3"
                    query_params="$4"
                    body="$5"

                    # Validate endpoint/method
                    if ! is_valid_api "$method" "$endpoint"; then
                        echo "❌ Error: Invalid API endpoint or method: $method $endpoint"
                        print_valid_endpoints
                        # Suggest closest match (simple fuzzy)
                        echo "\nHint: Did you mean one of these?"
                        echo "$VALID_ENDPOINTS" | grep "$endpoint" | grep "$method" || echo "$VALID_ENDPOINTS" | grep "$endpoint" || echo "$VALID_ENDPOINTS" | grep "$method" || echo "(see full list above)"
                        exit 1
                    fi

                    echo "Making API call: $method $endpoint"
                    
                    # Build URL with query parameters
                    full_url="$OBSERVE_BASE_URL$endpoint"
                    if [ -n "$query_params" ]; then
                        full_url="$full_url?$query_params"
                    fi
                    
                    echo "DEBUG: Executing $method request to $full_url"
                    response=$(execute_curl "$method" "$full_url" "$body")
                    ;;
                *)
                    echo "Error: Unknown operation: $OPERATION"
                    echo "Supported operations: dataset, monitors, monitor-mute-rules, referencetables, query, api, advanced-query"
                    exit 1
                    ;;
            esac
            
            # Check if curl command was successful and capture any errors
            curl_exit_code=$?
            if [ $curl_exit_code -ne 0 ]; then
                echo "❌ Error: Failed to execute API call"
                echo ""
                echo "=== Debug Information ==="
                echo "Command: $command"
                echo "Operation: $OPERATION"
                echo "Sub-operation: $SUB_OPERATION"
                echo "Base URL: $OBSERVE_BASE_URL"
                echo "Curl Exit Code: $curl_exit_code"
                echo ""
                
                # Provide a simple error message based on common curl issues
                if [ $curl_exit_code -eq 6 ]; then
                    echo "❌ Network Error: Could not resolve host"
                    echo "Check if the base URL is correct: $OBSERVE_BASE_URL"
                elif [ $curl_exit_code -eq 7 ]; then
                    echo "❌ Network Error: Failed to connect to host"
                    echo "Check network connectivity to: $OBSERVE_BASE_URL"
                elif [ $curl_exit_code -eq 28 ]; then
                    echo "❌ Timeout Error: Request timed out"
                    echo "The request took too long. Check network connectivity."
                elif [ $curl_exit_code -eq 35 ]; then
                    echo "❌ SSL Error: SSL/TLS connection failed"
                    echo "Check if the endpoint supports HTTPS."
                elif [ $curl_exit_code -eq 127 ]; then
                    echo "❌ Command Error: curl command not found"
                    echo "The curl command is not available in this environment."
                else
                    echo "❌ Curl Error: Exit code $curl_exit_code"
                fi
                
                echo ""
                echo "=== Troubleshooting Steps ==="
                echo "1. Check if OBSERVE_API_KEY is set correctly"
                echo "2. Check if OBSERVE_CUSTOMER_ID is set correctly"
                echo "3. Verify network connectivity to $OBSERVE_BASE_URL"
                echo "4. Check if the endpoint exists and is accessible"
                echo "5. Ensure Bearer token format is correct: 'Bearer <customerid> <token>'"
                echo ""
                
                # Test authentication
                echo "=== Authentication Test ==="
                if [ -n "$OBSERVE_API_KEY" ]; then
                    echo "✅ API Token is set (length: ${#OBSERVE_API_KEY} characters)"
                else
                    echo "❌ API Token is not set"
                fi
                
                if [ -n "$OBSERVE_CUSTOMER_ID" ]; then
                    echo "✅ Customer ID is set: $OBSERVE_CUSTOMER_ID"
                else
                    echo "❌ Customer ID is not set"
                fi
                
                echo "✅ Bearer token format: Bearer $OBSERVE_CUSTOMER_ID <token>"
                
                exit 1
            fi
            
            # Parse response to separate body and metadata
            # Extract metadata between METADATA_START and METADATA_END
            metadata=$(echo "$response" | sed -n '/METADATA_START/,/METADATA_END/p' | grep -v "METADATA_START\|METADATA_END")
            # Extract response body (everything after METADATA_END)
            response_body=$(echo "$response" | sed -n '/METADATA_END/,$p' | sed '1d')
            
            # Extract HTTP status code and response time from metadata
            http_status=$(echo "$metadata" | grep "HTTP_STATUS:" | sed 's/.*HTTP_STATUS://' | tr -d ' ')
            response_time=$(echo "$metadata" | grep "RESPONSE_TIME:" | sed 's/.*RESPONSE_TIME://' | tr -d ' ')
            
            echo "=== Response ==="
            echo "HTTP Status: $http_status"
            echo "Response Time: ${response_time}s"
            echo ""
            
            # Enhanced error handling with detailed information
            if [ "$http_status" -ge 200 ] && [ "$http_status" -lt 300 ]; then
                echo "✅ Success ($http_status)"
            elif [ "$http_status" -ge 400 ] && [ "$http_status" -lt 500 ]; then
                echo "❌ Client Error ($http_status)"
                echo ""
                echo "=== Error Details ==="
                case "$http_status" in
                    400)
                        echo "Bad Request - The request was malformed or invalid"
                        ;;
                    401)
                        echo "Unauthorized - Invalid or missing API key"
                        echo "Please check your OBSERVE_API_KEY environment variable"
                        ;;
                    403)
                        echo "Forbidden - Insufficient permissions for this operation"
                        echo "Please check your API key permissions"
                        ;;
                    404)
                        echo "Not Found - The requested resource was not found"
                        echo "Please verify the endpoint or resource ID"
                        ;;
                    409)
                        echo "Conflict - The request conflicts with current state"
                        ;;
                    422)
                        echo "Unprocessable Entity - The request was well-formed but contains invalid parameters"
                        ;;
                    429)
                        echo "Too Many Requests - Rate limit exceeded"
                        echo "Please wait before making additional requests"
                        ;;
                    *)
                        echo "Client Error - HTTP $http_status"
                        ;;
                esac
                
                # Try to extract error details from response body
                if command -v jq >/dev/null 2>&1; then
                    error_message=$(echo "$response_body" | jq -r '.error // .message // .detail // "No error message provided"' 2>/dev/null)
                    if [ "$error_message" != "null" ] && [ "$error_message" != "No error message provided" ]; then
                        echo ""
                        echo "Error Message: $error_message"
                    fi
                    
                    # Extract additional error details if available
                    error_code=$(echo "$response_body" | jq -r '.code // .error_code // "N/A"' 2>/dev/null)
                    if [ "$error_code" != "null" ] && [ "$error_code" != "N/A" ]; then
                        echo "Error Code: $error_code"
                    fi
                    
                    # Show full error response for debugging
                    echo ""
                    echo "=== Full Error Response ==="
                    echo "$response_body" | jq '.' 2>/dev/null || echo "$response_body"
                else
                    echo ""
                    echo "=== Full Error Response ==="
                    echo "$response_body"
                fi
                
                exit 1
            elif [ "$http_status" -ge 500 ]; then
                echo "❌ Server Error ($http_status)"
                echo ""
                echo "=== Error Details ==="
                case "$http_status" in
                    500)
                        echo "Internal Server Error - The server encountered an unexpected condition"
                        ;;
                    502)
                        echo "Bad Gateway - The server received an invalid response from upstream"
                        ;;
                    503)
                        echo "Service Unavailable - The service is temporarily unavailable"
                        echo "Please try again later"
                        ;;
                    504)
                        echo "Gateway Timeout - The server did not receive a timely response"
                        ;;
                    *)
                        echo "Server Error - HTTP $http_status"
                        ;;
                esac
                
                # Try to extract error details from response body
                if command -v jq >/dev/null 2>&1; then
                    error_message=$(echo "$response_body" | jq -r '.error // .message // .detail // "No error message provided"' 2>/dev/null)
                    if [ "$error_message" != "null" ] && [ "$error_message" != "No error message provided" ]; then
                        echo ""
                        echo "Error Message: $error_message"
                    fi
                    
                    # Show full error response for debugging
                    echo ""
                    echo "=== Full Error Response ==="
                    echo "$response_body" | jq '.' 2>/dev/null || echo "$response_body"
                else
                    echo ""
                    echo "=== Full Error Response ==="
                    echo "$response_body"
                fi
                
                exit 1
            else
                echo "⚠️  Unexpected Status ($http_status)"
                echo ""
                echo "=== Response Details ==="
                if command -v jq >/dev/null 2>&1; then
                    echo "$response_body" | jq '.' 2>/dev/null || echo "$response_body"
                else
                    echo "$response_body"
                fi
            fi
            echo ""
            
            # Truncate output if too large
            MAX_LINES=100
            MAX_CHARS=10000
            num_lines=$(echo "$response_body" | wc -l | tr -d ' ')
            num_chars=$(echo "$response_body" | wc -c | tr -d ' ')
            if [ "$num_lines" -gt "$MAX_LINES" ]; then
                echo "⚠️  Output truncated to $MAX_LINES lines. Refine your query or use filters for more data."
                response_body=$(echo "$response_body" | head -n $MAX_LINES)
            fi
            if [ "$num_chars" -gt "$MAX_CHARS" ]; then
                echo "⚠️  Output truncated to $MAX_CHARS characters. Refine your query or use filters for more data."
                response_body=$(echo "$response_body" | head -c $MAX_CHARS)
            fi
            
            # Try to format JSON response, fallback to raw if not JSON
            if command -v jq >/dev/null 2>&1; then
                echo "$response_body" | jq '.' 2>/dev/null || echo "$response_body"
            else
                echo "$response_body"
            fi
            """,
            args=[
                Arg(name="command", description="The command to execute (e.g., 'datasets list', 'monitors show <id>', 'query <dataset-id> <oql-query>', 'api GET /v1/dataset')", required=True)
            ],
            image="alpine:latest"
        )

CLITools() 