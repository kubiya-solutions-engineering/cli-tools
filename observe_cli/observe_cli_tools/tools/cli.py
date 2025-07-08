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
                echo "  'advanced-query <dataset-id> [options]' - Advanced query with filters and parameters"
                echo ""
                echo "Advanced URL Parameters:"
                echo "  Time ranges: time-start, time-end, time-preset"
                echo "  Filters: filter-<column>=<value>, filter=<column>|<operator>|<value>"
                echo "  OPAL: opal=<opal-statement>"
                echo "  Parameters: param-<key>=<value>"
                echo "  Tabs: v-tab=<tab-name>"
                echo "  Dashboard: v-dash=<dashboard-id>"
                echo ""
                echo "Advanced Query Examples:"
                echo "  advanced-query dataset-123 --time-preset PAST_1_HOUR"
                echo "  advanced-query dataset-123 --filter-eq status error"
                echo "  advanced-query dataset-123 --filter severity != warning"
                echo "  advanced-query dataset-123 --opal 'filter severity == \"error\"'"
                echo "  advanced-query dataset-123 --time-start 1686165391864 --time-end 1686251791864"
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
                "advanced-query")
                    if [ -z "$2" ]; then
                        echo "Error: Advanced query requires dataset ID"
                        echo "Usage: advanced-query <dataset-id> [options]"
                        echo ""
                        echo "Options:"
                        echo "  --time-start <timestamp>     Start time (Unix epoch or ISO 8601)"
                        echo "  --time-end <timestamp>       End time (Unix epoch or ISO 8601)"
                        echo "  --time-preset <preset>       Time preset (TODAY, YESTERDAY, etc.)"
                        echo "  --filter <column> <operator> <value>  Filter with operator"
                        echo "  --filter-eq <column> <value> Filter with equals"
                        echo "  --opal <opal-statement>      OPAL statement"
                        echo "  --param <key> <value>        Parameter"
                        echo "  --tab <tab-name>             Tab selection"
                        echo "  --dash <dashboard-id>        Dashboard selection"
                        echo ""
                        echo "Examples:"
                        echo "  advanced-query dataset-123 --time-preset PAST_1_HOUR"
                        echo "  advanced-query dataset-123 --filter-eq status error"
                        echo "  advanced-query dataset-123 --filter severity != warning"
                        echo "  advanced-query dataset-123 --opal 'filter severity == \"error\"'"
                        exit 1
                    fi
                    
                    dataset_id="$2"
                    shift 2
                    
                    # Parse advanced options
                    while [ $# -gt 0 ]; do
                        case "$1" in
                            --time-start)
                                time_start="$2"
                                shift 2
                                ;;
                            --time-end)
                                time_end="$2"
                                shift 2
                                ;;
                            --time-preset)
                                time_preset="$2"
                                shift 2
                                ;;
                            --filter)
                                filter_column="$2"
                                filter_operator="$3"
                                filter_value="$4"
                                shift 4
                                ;;
                            --filter-eq)
                                filter_column="$2"
                                filter_value="$3"
                                shift 3
                                ;;
                            --opal)
                                opal="$2"
                                shift 2
                                ;;
                            --param)
                                param_key="$2"
                                param_value="$3"
                                shift 3
                                ;;
                            --tab)
                                v_tab="$2"
                                shift 2
                                ;;
                            --dash)
                                v_dash="$2"
                                shift 2
                                ;;
                            *)
                                echo "Error: Unknown option $1"
                                exit 1
                                ;;
                        esac
                    done
                    
                    echo "Executing advanced query on dataset: $dataset_id"
                    
                    # Build query parameters
                    query_params=$(build_query_params)
                    
                    # Build the URL
                    full_url="$OBSERVE_BASE_URL/v1/datasets/$dataset_id"
                    if [ -n "$query_params" ]; then
                        full_url="$full_url?$query_params"
                        echo "Query parameters: $query_params"
                    fi
                    
                    echo "Full URL: $full_url"
                    echo ""
                    
                    # Execute the query
                    response=$(curl -s -w '\\nHTTP_STATUS:%{http_code}\\nRESPONSE_TIME:%{time_total}s' $HEADERS "$full_url")
                    ;;
                *)
                    echo "Error: Unknown operation: $OPERATION"
                    echo "Supported operations: datasets, monitors, dashboards, resources, events, query, api, advanced-query"
                    exit 1
                    ;;
            esac
            
            # Check if curl command was successful and capture any errors
            curl_exit_code=$?
            if [ $curl_exit_code -ne 0 ]; then
                echo "Error: Failed to execute API call (curl exit code: $curl_exit_code)"
                echo ""
                echo "=== Debug Information ==="
                echo "Command: $command"
                echo "Operation: $OPERATION"
                echo "Sub-operation: $SUB_OPERATION"
                echo "Base URL: $OBSERVE_BASE_URL"
                echo "Headers: $HEADERS"
                echo "Curl Exit Code: $curl_exit_code"
                echo ""
                
                # Provide specific error messages based on curl exit codes
                case $curl_exit_code in
                    1)
                        echo "❌ Curl Error 1: Unsupported protocol"
                        ;;
                    2)
                        echo "❌ Curl Error 2: Failed to initialize"
                        ;;
                    3)
                        echo "❌ Curl Error 3: URL malformed"
                        ;;
                    4)
                        echo "❌ Curl Error 4: URL user part was malformed"
                        ;;
                    5)
                        echo "❌ Curl Error 5: Couldn't resolve proxy"
                        ;;
                    6)
                        echo "❌ Curl Error 6: Couldn't resolve host"
                        echo "Check if the base URL is correct: $OBSERVE_BASE_URL"
                        ;;
                    7)
                        echo "❌ Curl Error 7: Failed to connect to host"
                        echo "Check network connectivity to: $OBSERVE_BASE_URL"
                        ;;
                    8)
                        echo "❌ Curl Error 8: Weird server reply"
                        ;;
                    9)
                        echo "❌ Curl Error 9: Remote access denied"
                        ;;
                    10)
                        echo "❌ Curl Error 10: FTP accept failed"
                        ;;
                    11)
                        echo "❌ Curl Error 11: FTP weird PASS reply"
                        ;;
                    12)
                        echo "❌ Curl Error 12: FTP weird USER reply"
                        ;;
                    13)
                        echo "❌ Curl Error 13: FTP weird PASV reply"
                        ;;
                    14)
                        echo "❌ Curl Error 14: FTP weird 227 format"
                        ;;
                    15)
                        echo "❌ Curl Error 15: FTP can't get host"
                        ;;
                    16)
                        echo "❌ Curl Error 16: HTTP/2 error"
                        ;;
                    17)
                        echo "❌ Curl Error 17: FTP couldn't set binary"
                        ;;
                    18)
                        echo "❌ Curl Error 18: Partial file"
                        ;;
                    19)
                        echo "❌ Curl Error 19: FTP couldn't download/access the given file"
                        ;;
                    20)
                        echo "❌ Curl Error 20: FTP write error"
                        ;;
                    21)
                        echo "❌ Curl Error 21: FTP read error"
                        ;;
                    22)
                        echo "❌ Curl Error 22: FTP quote error"
                        ;;
                    23)
                        echo "❌ Curl Error 23: HTTP page not retrieved"
                        ;;
                    25)
                        echo "❌ Curl Error 25: FTP couldn't STOR file"
                        ;;
                    26)
                        echo "❌ Curl Error 26: Read error"
                        ;;
                    27)
                        echo "❌ Curl Error 27: Out of memory"
                        ;;
                    28)
                        echo "❌ Curl Error 28: Operation timeout"
                        echo "The request timed out. Check network connectivity."
                        ;;
                    30)
                        echo "❌ Curl Error 30: FTP PORT failed"
                        ;;
                    31)
                        echo "❌ Curl Error 31: FTP couldn't use REST"
                        ;;
                    33)
                        echo "❌ Curl Error 33: HTTP range error"
                        ;;
                    34)
                        echo "❌ Curl Error 34: HTTP post error"
                        ;;
                    35)
                        echo "❌ Curl Error 35: SSL connect error"
                        echo "SSL/TLS connection failed. Check if the endpoint supports HTTPS."
                        ;;
                    36)
                        echo "❌ Curl Error 36: Bad download resume"
                        ;;
                    37)
                        echo "❌ Curl Error 37: FILE couldn't read file"
                        ;;
                    38)
                        echo "❌ Curl Error 38: LDAP cannot bind"
                        ;;
                    39)
                        echo "❌ Curl Error 39: LDAP search failed"
                        ;;
                    41)
                        echo "❌ Curl Error 41: Function not found"
                        ;;
                    42)
                        echo "❌ Curl Error 42: Aborted by callback"
                        ;;
                    43)
                        echo "❌ Curl Error 43: Bad function argument"
                        ;;
                    45)
                        echo "❌ Curl Error 45: Interface failed"
                        ;;
                    47)
                        echo "❌ Curl Error 47: Too many redirects"
                        ;;
                    48)
                        echo "❌ Curl Error 48: Unknown option specified to libcurl"
                        ;;
                    49)
                        echo "❌ Curl Error 49: Malformed telnet option"
                        ;;
                    51)
                        echo "❌ Curl Error 51: The peer's SSL certificate or SSH MD5 fingerprint was not OK"
                        ;;
                    52)
                        echo "❌ Curl Error 52: The server didn't reply anything"
                        ;;
                    53)
                        echo "❌ Curl Error 53: SSL crypto engine not found"
                        ;;
                    54)
                        echo "❌ Curl Error 54: Cannot set SSL crypto engine as default"
                        ;;
                    55)
                        echo "❌ Curl Error 55: Failed sending network data"
                        ;;
                    56)
                        echo "❌ Curl Error 56: Failure in receiving network data"
                        ;;
                    58)
                        echo "❌ Curl Error 58: Problem with the local certificate"
                        ;;
                    59)
                        echo "❌ Curl Error 59: Couldn't use specified SSL cipher"
                        ;;
                    60)
                        echo "❌ Curl Error 60: Peer certificate cannot be authenticated with known CA certificates"
                        ;;
                    61)
                        echo "❌ Curl Error 61: Unrecognized transfer encoding"
                        ;;
                    62)
                        echo "❌ Curl Error 62: Invalid LDAP URL"
                        ;;
                    63)
                        echo "❌ Curl Error 63: Maximum file size exceeded"
                        ;;
                    64)
                        echo "❌ Curl Error 64: Requested FTP SSL level failed"
                        ;;
                    65)
                        echo "❌ Curl Error 65: Sending the data requires a rewind that failed"
                        ;;
                    66)
                        echo "❌ Curl Error 66: Failed to initialise SSL engine"
                        ;;
                    67)
                        echo "❌ Curl Error 67: The user name, password, or similar was not accepted and curl failed to log in"
                        ;;
                    68)
                        echo "❌ Curl Error 68: File not found on TFTP server"
                        ;;
                    69)
                        echo "❌ Curl Error 69: Permission problem on TFTP server"
                        ;;
                    70)
                        echo "❌ Curl Error 70: Out of disk space on TFTP server"
                        ;;
                    71)
                        echo "❌ Curl Error 71: Illegal TFTP operation"
                        ;;
                    72)
                        echo "❌ Curl Error 72: Unknown TFTP transfer ID"
                        ;;
                    73)
                        echo "❌ Curl Error 73: File already exists (TFTP)"
                        ;;
                    74)
                        echo "❌ Curl Error 74: No such user (TFTP)"
                        ;;
                    75)
                        echo "❌ Curl Error 75: Character conversion failed"
                        ;;
                    76)
                        echo "❌ Curl Error 76: Character conversion functions required"
                        ;;
                    77)
                        echo "❌ Curl Error 77: Problem with reading the SSL CA cert"
                        ;;
                    78)
                        echo "❌ Curl Error 78: The resource referenced in the URL does not exist"
                        ;;
                    79)
                        echo "❌ Curl Error 79: An unspecified error occurred during the SSH session"
                        ;;
                    80)
                        echo "❌ Curl Error 80: Failed to shut down the SSL connection"
                        ;;
                    82)
                        echo "❌ Curl Error 82: Could not load CRL file"
                        ;;
                    83)
                        echo "❌ Curl Error 83: Issuer check failed"
                        ;;
                    84)
                        echo "❌ Curl Error 84: The FTP PRET command failed"
                        ;;
                    85)
                        echo "❌ Curl Error 85: RTSP: mismatch of CSeq numbers"
                        ;;
                    86)
                        echo "❌ Curl Error 86: RTSP: mismatch of Session Identifiers"
                        ;;
                    87)
                        echo "❌ Curl Error 87: unable to parse FTP file list"
                        ;;
                    88)
                        echo "❌ Curl Error 88: FTP chunk callback reported error"
                        ;;
                    89)
                        echo "❌ Curl Error 89: No connection available, the session will be queued"
                        ;;
                    90)
                        echo "❌ Curl Error 90: SSL public key does not matched pinned public key"
                        ;;
                    91)
                        echo "❌ Curl Error 91: Invalid SSL certificate status"
                        ;;
                    92)
                        echo "❌ Curl Error 92: Stream error in HTTP/2 framing layer"
                        ;;
                    93)
                        echo "❌ Curl Error 93: An API function was called from inside a callback"
                        ;;
                    94)
                        echo "❌ Curl Error 94: An authentication function returned an error"
                        ;;
                    95)
                        echo "❌ Curl Error 95: A problem was detected in the HTTP/3 layer"
                        ;;
                    96)
                        echo "❌ Curl Error 96: QUIC connection error"
                        ;;
                    97)
                        echo "❌ Curl Error 97: Proxy handshake error"
                        ;;
                    98)
                        echo "❌ Curl Error 98: A client-side certificate is required to complete the TLS handshake"
                        ;;
                    *)
                        echo "❌ Curl Error $curl_exit_code: Unknown error"
                        ;;
                esac
                
                echo ""
                echo "=== Troubleshooting Steps ==="
                echo "1. Check if OBSERVE_API_KEY is set correctly"
                echo "2. Check if OBSERVE_CUSTOMER_ID is set correctly"
                echo "3. Verify network connectivity to $OBSERVE_BASE_URL"
                echo "4. Check if the endpoint exists and is accessible"
                echo "5. Verify SSL/TLS connectivity (if using HTTPS)"
                echo "6. Ensure Bearer token format is correct: 'Bearer <customerid> <token>'"
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
                
                # Try a simple connectivity test
                echo "=== Connectivity Test ==="
                if curl -s --connect-timeout 10 --max-time 30 "$OBSERVE_BASE_URL" >/dev/null 2>&1; then
                    echo "✅ Base URL is reachable"
                else
                    echo "❌ Cannot reach base URL - check network connectivity"
                fi
                
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