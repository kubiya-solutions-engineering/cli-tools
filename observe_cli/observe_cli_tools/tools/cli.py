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
            description="Execute any Observe API operation with dynamic parameters and proper response parsing",
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
            
            # Set base URL
            OBSERVE_BASE_URL="https://$OBSERVE_CUSTOMER_ID.collect.observeinc.com"
            
            # Set default headers
            HEADERS="-H 'Authorization: Bearer $OBSERVE_API_KEY' -H 'Content-Type: application/json'"
            
            # Parse the command to determine operation type
            if [ -z "$command" ]; then
                echo "Error: Command is required"
                echo "Usage examples:"
                echo "  'datasets list' - List all datasets"
                echo "  'datasets show <dataset-id>' - Show dataset details"
                echo "  'monitors list' - List all monitors"
                echo "  'monitors show <monitor-id>' - Show monitor details"
                echo "  'dashboards list' - List all dashboards"
                echo "  'resources list' - List all resources"
                echo "  'events list' - List all events"
                echo "  'query <dataset-id> <oql-query>' - Execute OQL query"
                echo "  'api <method> <endpoint> [query-params] [body]' - Custom API call"
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
                "datasets")
                    case "$SUB_OPERATION" in
                        "list")
                            echo "Listing datasets..."
                            response=$(curl -s -w '\\nHTTP_STATUS:%{http_code}\\nRESPONSE_TIME:%{time_total}s' $HEADERS "$OBSERVE_BASE_URL/v1/datasets")
                            ;;
                        "show")
                            if [ -z "$3" ]; then
                                echo "Error: Dataset ID is required for 'datasets show'"
                                exit 1
                            fi
                            dataset_id="$3"
                            echo "Showing dataset: $dataset_id"
                            response=$(curl -s -w '\\nHTTP_STATUS:%{http_code}\\nRESPONSE_TIME:%{time_total}s' $HEADERS "$OBSERVE_BASE_URL/v1/datasets/$dataset_id")
                            ;;
                        *)
                            echo "Error: Unknown datasets operation: $SUB_OPERATION"
                            echo "Supported: list, show"
                            exit 1
                            ;;
                    esac
                    ;;
                "monitors")
                    case "$SUB_OPERATION" in
                        "list")
                            echo "Listing monitors..."
                            response=$(curl -s -w '\\nHTTP_STATUS:%{http_code}\\nRESPONSE_TIME:%{time_total}s' $HEADERS "$OBSERVE_BASE_URL/v1/monitors")
                            ;;
                        "show")
                            if [ -z "$3" ]; then
                                echo "Error: Monitor ID is required for 'monitors show'"
                                exit 1
                            fi
                            monitor_id="$3"
                            echo "Showing monitor: $monitor_id"
                            response=$(curl -s -w '\\nHTTP_STATUS:%{http_code}\\nRESPONSE_TIME:%{time_total}s' $HEADERS "$OBSERVE_BASE_URL/v1/monitors/$monitor_id")
                            ;;
                        *)
                            echo "Error: Unknown monitors operation: $SUB_OPERATION"
                            echo "Supported: list, show"
                            exit 1
                            ;;
                    esac
                    ;;
                "dashboards")
                    case "$SUB_OPERATION" in
                        "list")
                            echo "Listing dashboards..."
                            response=$(curl -s -w '\\nHTTP_STATUS:%{http_code}\\nRESPONSE_TIME:%{time_total}s' $HEADERS "$OBSERVE_BASE_URL/v1/dashboards")
                            ;;
                        "show")
                            if [ -z "$3" ]; then
                                echo "Error: Dashboard ID is required for 'dashboards show'"
                                exit 1
                            fi
                            dashboard_id="$3"
                            echo "Showing dashboard: $dashboard_id"
                            response=$(curl -s -w '\\nHTTP_STATUS:%{http_code}\\nRESPONSE_TIME:%{time_total}s' $HEADERS "$OBSERVE_BASE_URL/v1/dashboards/$dashboard_id")
                            ;;
                        *)
                            echo "Error: Unknown dashboards operation: $SUB_OPERATION"
                            echo "Supported: list, show"
                            exit 1
                            ;;
                    esac
                    ;;
                "resources")
                    case "$SUB_OPERATION" in
                        "list")
                            echo "Listing resources..."
                            response=$(curl -s -w '\\nHTTP_STATUS:%{http_code}\\nRESPONSE_TIME:%{time_total}s' $HEADERS "$OBSERVE_BASE_URL/v1/resources")
                            ;;
                        "show")
                            if [ -z "$3" ]; then
                                echo "Error: Resource ID is required for 'resources show'"
                                exit 1
                            fi
                            resource_id="$3"
                            echo "Showing resource: $resource_id"
                            response=$(curl -s -w '\\nHTTP_STATUS:%{http_code}\\nRESPONSE_TIME:%{time_total}s' $HEADERS "$OBSERVE_BASE_URL/v1/resources/$resource_id")
                            ;;
                        *)
                            echo "Error: Unknown resources operation: $SUB_OPERATION"
                            echo "Supported: list, show"
                            exit 1
                            ;;
                    esac
                    ;;
                "events")
                    case "$SUB_OPERATION" in
                        "list")
                            echo "Listing events..."
                            response=$(curl -s -w '\\nHTTP_STATUS:%{http_code}\\nRESPONSE_TIME:%{time_total}s' $HEADERS "$OBSERVE_BASE_URL/v1/events")
                            ;;
                        "show")
                            if [ -z "$3" ]; then
                                echo "Error: Event ID is required for 'events show'"
                                exit 1
                            fi
                            event_id="$3"
                            echo "Showing event: $event_id"
                            response=$(curl -s -w '\\nHTTP_STATUS:%{http_code}\\nRESPONSE_TIME:%{time_total}s' $HEADERS "$OBSERVE_BASE_URL/v1/events/$event_id")
                            ;;
                        *)
                            echo "Error: Unknown events operation: $SUB_OPERATION"
                            echo "Supported: list, show"
                            exit 1
                            ;;
                    esac
                    ;;
                "query")
                    if [ -z "$2" ] || [ -z "$3" ]; then
                        echo "Error: Query requires dataset ID and OQL query"
                        echo "Usage: query <dataset-id> <oql-query>"
                        exit 1
                    fi
                    dataset_id="$2"
                    # Get all remaining arguments as the query
                    shift 2
                    query="$*"
                    echo "Executing query on dataset: $dataset_id"
                    echo "Query: $query"
                    
                    # Prepare query payload
                    QUERY_PAYLOAD='{"query": "'$query'", "dataset": "'$dataset_id'"}'
                    response=$(curl -s -w '\\nHTTP_STATUS:%{http_code}\\nRESPONSE_TIME:%{time_total}s' -X POST $HEADERS -d "$QUERY_PAYLOAD" "$OBSERVE_BASE_URL/v1/query")
                    ;;
                "api")
                    if [ -z "$2" ] || [ -z "$3" ]; then
                        echo "Error: API call requires method and endpoint"
                        echo "Usage: api <method> <endpoint> [query-params] [body]"
                        exit 1
                    fi
                    method="$2"
                    endpoint="$3"
                    query_params="$4"
                    body="$5"
                    
                    echo "Making API call: $method $endpoint"
                    
                    # Build URL with query parameters
                    full_url="$OBSERVE_BASE_URL$endpoint"
                    if [ -n "$query_params" ]; then
                        full_url="$full_url?$query_params"
                    fi
                    
                    # Build curl command
                    CURL_CMD="curl -s -w '\\nHTTP_STATUS:%{http_code}\\nRESPONSE_TIME:%{time_total}s' $HEADERS"
                    case "$method" in
                        GET)
                            CURL_CMD="$CURL_CMD '$full_url'"
                            ;;
                        POST|PUT|PATCH)
                            if [ -n "$body" ]; then
                                CURL_CMD="$CURL_CMD -X $method -d '$body' '$full_url'"
                            else
                                CURL_CMD="$CURL_CMD -X $method '$full_url'"
                            fi
                            ;;
                        DELETE)
                            CURL_CMD="$CURL_CMD -X DELETE '$full_url'"
                            ;;
                        *)
                            echo "Error: Unsupported HTTP method: $method"
                            exit 1
                            ;;
                    esac
                    
                    response=$(eval $CURL_CMD)
                    ;;
                *)
                    echo "Error: Unknown operation: $OPERATION"
                    echo "Supported operations: datasets, monitors, dashboards, resources, events, query, api"
                    exit 1
                    ;;
            esac
            
            # Check if curl command was successful
            if [ $? -ne 0 ]; then
                echo "Error: Failed to execute API call"
                exit 1
            fi
            
            # Parse response to separate body and metadata
            http_status=$(echo "$response" | grep "HTTP_STATUS:" | cut -d':' -f2)
            response_time=$(echo "$response" | grep "RESPONSE_TIME:" | cut -d':' -f2)
            response_body=$(echo "$response" | sed '/HTTP_STATUS:/d' | sed '/RESPONSE_TIME:/d')
            
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
            
            # Try to format JSON response, fallback to raw if not JSON
            if command -v jq >/dev/null 2>&1; then
                echo "$response_body" | jq '.' 2>/dev/null || echo "$response_body"
            else
                echo "$response_body"
            fi
            """,
            args=[
                Arg(name="command", description="The command to execute (e.g., 'datasets list', 'monitors show <id>', 'query <dataset-id> <oql-query>', 'api GET /v1/datasets')", required=True)
            ],
            image="alpine:latest"
        )

CLITools() 