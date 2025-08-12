import sys
from .base import DatadogCLITool, Arg
from kubiya_sdk.tools.registry import tool_registry

class CLITools:
    """Datadog API and CLI wrapper tools."""

    def __init__(self):
        """Initialize and register all Datadog API tools."""
        try:
            tools = [
                self.list_monitors(),
                self.search_metrics()
            ]
            
            for tool in tools:
                try:
                    tool_registry.register("datadog_cli", tool)
                    print(f"✅ Registered: {tool.name}")
                except Exception as e:
                    print(f"❌ Failed to register {tool.name}: {str(e)}", file=sys.stderr)
                    raise
        except Exception as e:
            print(f"❌ Failed to register Datadog CLI tools: {str(e)}", file=sys.stderr)
            raise

    def list_monitors(self) -> DatadogCLITool:
        """List Datadog monitors with intelligent filtering options."""
        
        return DatadogCLITool(
            name="datadog_list_monitors",
            description="List Datadog monitors with filtering options to avoid timeouts and get specific results. Use filters to narrow down large datasets efficiently.",
            content="""
            set -e  # Exit on any error

            # Install datadog package if not already installed
            echo "Installing datadog package..."
            pip install datadog > /dev/null 2>&1
            echo "✅ Datadog package installed"

            # Find the dog command
            DOG_CMD=""
            if command -v dog &> /dev/null; then
                DOG_CMD="dog"
            else
                PYTHON_DIR="$(dirname $(which python))"
                if [ -f "$PYTHON_DIR/dog" ] && [ -x "$PYTHON_DIR/dog" ]; then
                    DOG_CMD="$PYTHON_DIR/dog"
                else
                    if python -c "import datadog.dogshell" &> /dev/null; then
                        DOG_CMD="python -m datadog.dogshell"
                    else
                        echo "❌ Error: Could not locate dog command"
                        exit 1
                    fi
                fi
            fi

            # Build the command with filters
            CMD="$DOG_CMD --application-key ${DD_APP_KEY} --api-key ${DD_API_KEY} --api_host ${DD_SITE} --timeout 120 monitor show_all"
            
            # Add filters if provided
            if [ -n "$group_states" ]; then
                CMD="$CMD --group_states $group_states"
            fi
            
            if [ -n "$name_filter" ]; then
                CMD="$CMD --name '$name_filter'"
            fi
            
            if [ -n "$tags" ]; then
                CMD="$CMD --tags '$tags'"
            fi
            
            if [ -n "$monitor_tags" ]; then
                CMD="$CMD --monitor_tags '$monitor_tags'"
            fi

            echo "=== Listing Datadog Monitors ==="
            echo "Command: $CMD"
            echo "Timestamp: $(date)"
            echo ""

            # Execute the command
            timeout 180 $CMD 2>&1
            exit_code=$?

            if [ $exit_code -eq 124 ]; then
                echo ""
                echo "❌ Command timed out after 180 seconds"
                echo "💡 Try using more specific filters to reduce the dataset size"
                exit 1
            elif [ $exit_code -eq 0 ]; then
                echo ""
                echo "✅ Monitors listed successfully"
            else
                echo ""
                echo "❌ Command failed with exit code $exit_code"
                echo "💡 Check your credentials and command syntax"
                exit $exit_code
            fi
            """,
            args=[
                Arg(
                    name="group_states", 
                    description="Filter by monitor states. Options: 'all', 'alert', 'warn', 'no_data'. Use comma-separated for multiple (e.g., 'alert,warn' to show only alerting monitors). Leave empty to show all states.",
                    required=False
                ),
                Arg(
                    name="name_filter", 
                    description="Filter monitors by name. Provide a string to search for in monitor names (e.g., 'api' to find all monitors with 'api' in the name). Case-insensitive partial matching.",
                    required=False
                ),
                Arg(
                    name="tags", 
                    description="Filter by scope tags. Format: 'key:value' or 'key1:value1,key2:value2'. Examples: 'env:production', 'service:api,env:staging'. These are tags on the resources being monitored.",
                    required=False
                ),
                Arg(
                    name="monitor_tags", 
                    description="Filter by monitor tags. Format: 'key:value' or 'key1:value1,key2:value2'. Examples: 'team:backend', 'priority:high,team:frontend'. These are tags applied to the monitors themselves.",
                    required=False
                )
            ],
            image="python:3.9-slim"
        )

    def search_metrics(self) -> DatadogCLITool:
        """Search and query Datadog metrics using the API."""
        
        return DatadogCLITool(
            name="datadog_search_metrics",
            description="Search and query Datadog metrics using the API. Supports metric search, timeseries queries, and active metric listing.",
            content="""
            set -e  # Exit on any error

            # Install required packages
            echo "Installing required packages..."
            pip install requests > /dev/null 2>&1
            echo "✅ Required packages installed"

            # Create Python script for API calls
            cat << 'EOF' > /tmp/datadog_metrics.py
import requests
import json
import sys
import os
import argparse
from datetime import datetime, timedelta

class DatadogMetricsAPI:
    def __init__(self):
        self.api_key = os.environ.get('DD_API_KEY')
        self.app_key = os.environ.get('DD_APP_KEY')
        self.site = os.environ.get('DD_SITE', 'api.datadoghq.com')
        
        if not self.api_key or not self.app_key:
            print("❌ Error: DD_API_KEY and DD_APP_KEY environment variables are required")
            sys.exit(1)
        
        # Handle both full URLs and hostname-only formats
        if self.site.startswith('http://') or self.site.startswith('https://'):
            self.base_url = self.site
        else:
            self.base_url = f"https://{self.site}"
        self.headers = {
            "DD-API-KEY": self.api_key,
            "DD-APPLICATION-KEY": self.app_key,
            "Content-Type": "application/json"
        }

    def search_metrics(self, query):
        # Search for metrics by name/pattern
        url = f"{self.base_url}/api/v1/search"
        params = {"q": f"metrics:{query}"}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            metrics = data.get('results', {}).get('metrics', [])
            
            print(f"Found {len(metrics)} metrics matching '{query}':")
            print("=" * 50)
            for metric in metrics:
                print(f"📊 {metric}")
            
            return metrics
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error searching metrics: {str(e)}")
            sys.exit(1)

    def query_timeseries(self, query, start_time=None, end_time=None):
        # Query timeseries data for a metric
        url = f"{self.base_url}/api/v1/query"
        
        # Default to last hour if no time range specified
        if not end_time:
            end_time = int(datetime.now().timestamp())
        if not start_time:
            start_time = int((datetime.now() - timedelta(hours=1)).timestamp())
        
        params = {
            "query": query,
            "from": start_time,
            "to": end_time
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            print(f"Query: {query}")
            print(f"Time range: {datetime.fromtimestamp(start_time)} to {datetime.fromtimestamp(end_time)}")
            print("=" * 70)
            
            if 'series' in data and data['series']:
                for series in data['series']:
                    print(f"📈 Metric: {series.get('metric', 'Unknown')}")
                    if series.get('tag_set'):
                        print(f"   Tags: {', '.join(series['tag_set'])}")
                    
                    points = series.get('pointlist', [])
                    if points:
                        print(f"   Data points: {len(points)}")
                        print(f"   Latest value: {points[-1][1]} at {datetime.fromtimestamp(points[-1][0]/1000)}")
                        
                        # Show first few and last few points if many
                        if len(points) > 10:
                            print("   Sample points:")
                            for i, (timestamp, value) in enumerate(points[:3]):
                                print(f"     {datetime.fromtimestamp(timestamp/1000)}: {value}")
                            print("     ...")
                            for i, (timestamp, value) in enumerate(points[-3:]):
                                print(f"     {datetime.fromtimestamp(timestamp/1000)}: {value}")
                        else:
                            print("   All points:")
                            for timestamp, value in points:
                                print(f"     {datetime.fromtimestamp(timestamp/1000)}: {value}")
                    print()
            else:
                print("No data found for the specified query and time range.")
            
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error querying timeseries: {str(e)}")
            sys.exit(1)

    def list_active_metrics(self, hours_ago=24):
        # List active metrics from the last N hours
        url = f"{self.base_url}/api/v1/metrics"
        from_time = int((datetime.now() - timedelta(hours=hours_ago)).timestamp())
        
        params = {"from": from_time}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            metrics = data.get('metrics', [])
            
            print(f"Found {len(metrics)} active metrics from the last {hours_ago} hours:")
            print("=" * 60)
            
            # Group metrics by common prefixes for better readability
            metric_groups = {}
            for metric in metrics:
                prefix = metric.split('.')[0] if '.' in metric else metric
                if prefix not in metric_groups:
                    metric_groups[prefix] = []
                metric_groups[prefix].append(metric)
            
            for prefix, group_metrics in sorted(metric_groups.items()):
                print(f"\\n📊 {prefix}.* ({len(group_metrics)} metrics):")
                for metric in sorted(group_metrics):
                    print(f"   - {metric}")
            
            return metrics
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error listing active metrics: {str(e)}")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Datadog Metrics API Tool')
    parser.add_argument('--operation', required=True, choices=['search', 'query', 'list'],
                       help='Operation to perform: search, query, or list')
    parser.add_argument('--query', help='For search: metric name pattern. For query: timeseries query')
    parser.add_argument('--start_time', type=int, help='For query: Unix timestamp for start time')
    parser.add_argument('--end_time', type=int, help='For query: Unix timestamp for end time')
    parser.add_argument('--hours', type=int, default=24, help='For list: hours to look back (default: 24)')
    
    args = parser.parse_args()
    api = DatadogMetricsAPI()
    
    if args.operation == "search":
        if not args.query:
            print("❌ Error: --query is required for search operation")
            sys.exit(1)
        api.search_metrics(args.query)
        
    elif args.operation == "query":
        if not args.query:
            print("❌ Error: --query is required for query operation")
            sys.exit(1)
        api.query_timeseries(args.query, args.start_time, args.end_time)
        
    elif args.operation == "list":
        api.list_active_metrics(args.hours)

if __name__ == "__main__":
    main()
EOF

            # Validate required parameters
            if [ -z "$operation" ]; then
                echo "❌ Error: Operation is required"
                echo ""
                echo "Usage: Specify the operation to perform"
                echo ""
                echo "Available operations:"
                echo "  • search --query <pattern>         - Search for metrics by name/pattern"
                echo "  • query --query <metric_query> [--start_time <timestamp>] [--end_time <timestamp>] - Query timeseries data"
                echo "  • list [--hours <number>]          - List active metrics (default: last 24 hours)"
                echo ""
                echo "Examples:"
                echo "  • search --query 'cpu'             - Find all metrics containing 'cpu'"
                echo "  • query --query 'avg:system.cpu.user' - Get CPU user time data"
                echo "  • query --query 'sum:nginx.requests{service:web-api}' --start_time -3600 - Get nginx request count for web-api service"
                echo "  • query --query 'avg:kubernetes.cpu.usage.total{*} by {prod-worker-1}' --start_time -3600 - Get CPU usage by node"
                echo "  • list                             - List all active metrics from last 24h"
                echo "  • list --hours 6                   - List metrics from last 6 hours"
                echo ""
                echo "💡 Note: When using queries from knowledge base, replace placeholders:"
                echo "  • {service} → service:actual-service-name"
                echo "  • {node} → node:actual-node-name"
                echo "  • {container_name} → container_name:actual-container-name"
                echo "  • {*} → specific tags like env:production,region:us-east-1"
                echo "  • For 'by' clauses, use the actual tag value: 'by {prod-worker-1}' not 'by {node}'"
                exit 1
            fi

            echo "=== Datadog Metrics API Operation ==="
            echo "Operation: $operation"
            echo "Timestamp: $(date)"
            echo "API Host: ${DD_SITE}"
            echo ""

            # Build command with named arguments, only including non-empty values
            CMD="python /tmp/datadog_metrics.py --operation \"$operation\""
            
            if [ -n "$query" ]; then
                CMD="$CMD --query \"$query\""
            fi
            
            if [ -n "$start_time" ]; then
                CMD="$CMD --start_time \"$start_time\""
            fi
            
            if [ -n "$end_time" ]; then
                CMD="$CMD --end_time \"$end_time\""
            fi
            
            # Execute the Python script with named arguments
            eval $CMD
            exit_code=$?

            if [ $exit_code -eq 0 ]; then
                echo ""
                echo "✅ Operation completed successfully"
            else
                echo ""
                echo "❌ Operation failed with exit code $exit_code"
                echo ""
                echo "💡 Troubleshooting tips:"
                echo "  • Check your DD_API_KEY and DD_APP_KEY credentials"
                echo "  • Verify DD_SITE is correct for your region"
                echo "  • Ensure you have proper permissions for the API"
                echo "  • Check metric names and query syntax"
                exit $exit_code
            fi

            # Clean up
            rm -f /tmp/datadog_metrics.py
            """,
            args=[
                Arg(name="operation", description="Operation to perform: 'search', 'query', or 'list'", required=True),
                Arg(name="query", description="For 'search': metric name pattern to search for. For 'query': timeseries query. IMPORTANT: Replace placeholders with actual values - use 'service:web-api' instead of '{service}', 'node:prod-1' instead of '{node}', etc. For 'by' clauses, use the actual tag value, not the tag name. Examples: 'avg:system.cpu.user', 'sum:nginx.requests{service:web-api}', 'avg:kubernetes.cpu.usage.total{*} by {prod-worker-1}'", required=False),
                Arg(name="start_time", description="For 'query': Unix timestamp for start time (optional, defaults to 1 hour ago)", required=False),
                Arg(name="end_time", description="For 'query': Unix timestamp for end time (optional, defaults to now)", required=False)
            ],
            image="python:3.9-slim"
        )

CLITools()