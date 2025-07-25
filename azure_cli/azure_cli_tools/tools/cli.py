from typing import List
import sys
from .base import AzureCLITool, Arg
from kubiya_sdk.tools.registry import tool_registry

class CLITools:
    """Azure CLI wrapper tools for AI-controlled Azure operations."""

    def __init__(self):
        """Initialize and register the Azure CLI tools."""
        try:
            # Register the main Azure CLI tool
            azure_tool = self.azure_cli()
            tool_registry.register("azure_cli", azure_tool)
            print(f"✅ Registered: {azure_tool.name}")
        except Exception as e:
            print(f"❌ Failed to register Azure CLI tools: {str(e)}", file=sys.stderr)
            raise

    def azure_cli(self) -> AzureCLITool:
        """A flexible Azure CLI wrapper that allows AI to execute any az command."""
        return AzureCLITool(
            name="azure_cli",
            description="Execute Azure CLI commands. Pass any 'az' command as the 'command' argument. The tool will handle authentication and execute the command, returning the output. Use --subscription parameter in your commands to specify which subscription to use. Examples: 'group list --subscription mySubscription', 'vm create --resource-group myRG --name myVM --image UbuntuLTS --subscription mySubscription', 'monitor app-insights query --app myApp --analytics-query \"requests | limit 10\" --subscription mySubscription', etc.",
            content="""
            # Validate environment variables
            if [ -z "$AZURE_CLIENT_ID" ]; then
                echo "❌ AZURE_CLIENT_ID environment variable is required"
                exit 1
            fi
            
            if [ -z "$AZURE_CLIENT_SECRET" ]; then
                echo "❌ AZURE_CLIENT_SECRET environment variable is required"
                exit 1
            fi
            
            if [ -z "$AZURE_TENANT_ID" ]; then
                echo "❌ AZURE_TENANT_ID environment variable is required"
                exit 1
            fi
            
            if [ -z "$command" ]; then
                echo "❌ Command argument is required"
                echo "Usage: Pass any 'az' command as the 'command' argument"
                echo "Examples:"
                echo "  command='group list --subscription mySubscription'"
                echo "  command='vm create --resource-group myRG --name myVM --image UbuntuLTS --subscription mySubscription'"
                echo "  command='monitor app-insights query --app myApp --analytics-query \"requests | limit 10\" --subscription mySubscription'"
                echo ""
                echo "💡 Use azure_subscriptions_list tool first to see available subscriptions"
                exit 1
            fi
            
            # Set up Azure CLI authentication using service principal
            echo "🔐 Authenticating with Azure..."
            az login --service-principal \\
                --username "$AZURE_CLIENT_ID" \\
                --password "$AZURE_CLIENT_SECRET" \\
                --tenant "$AZURE_TENANT_ID" >/dev/null 2>&1 || {
                echo "❌ Azure authentication failed"
                exit 1
            }
            
            # Parse the command
            cmd="$command"
            
            echo "🔧 Executing Azure CLI command: az $cmd"
            echo "----------------------------------------"
            
            # Execute the az command
            eval "az $cmd"
            
            exit_code=$?
            
            if [ $exit_code -eq 0 ]; then
                echo "----------------------------------------"
                echo "✅ Command executed successfully"
            else
                echo "----------------------------------------"
                echo "❌ Command failed with exit code: $exit_code"
                exit $exit_code
            fi
            """,
            args=[
                Arg(name="command", description="The Azure CLI command to execute (without 'az' prefix). Include --subscription parameter to specify which subscription to use. Examples: 'group list --subscription mySubscription', 'vm create --resource-group myRG --name myVM --image UbuntuLTS --subscription mySubscription', 'monitor app-insights query --app myApp --analytics-query \"requests | limit 10\" --subscription mySubscription'", required=True)
            ]
        )


# Initialize the CLI tools when the module is imported
cli_tools = CLITools() 