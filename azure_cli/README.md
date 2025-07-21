# Azure CLI Tools

A flexible Azure CLI wrapper tool for Kubiya, providing AI-controlled access to all Azure CLI functionality.

## Overview

This package provides a flexible tool that wraps the Azure CLI (`az`) command-line interface, allowing AI agents to execute any Azure CLI command through the Kubiya platform. Instead of multiple specific tools, this approach gives AI full control over the Azure CLI.

## Features

- **Full Azure CLI Access**: Execute any `az` command through a single tool
- **AI-Friendly**: Let AI construct the exact commands it needs
- **Flexible Subscriptions**: List and dynamically choose Azure subscriptions
- **Flexible**: Supports all current and future Azure CLI commands
- **Simple**: Two tools - one for listing subscriptions and one for executing commands
- **Fast & Reliable**: Uses official Microsoft Azure CLI Docker image
- **Authenticated**: Automatic Azure authentication handling

## Available Tools

### `azure_subscriptions_list`
List all Azure subscriptions available to the authenticated user. Use this first to discover which subscriptions you have access to.

**Parameters:**
- None required

**Example:**
```bash
azure_subscriptions_list
```

This will output a table showing all available subscriptions with their names, IDs, and status.

### `azure_cli`
Execute any Azure CLI command by passing the command as an argument.

**Parameters:**
- `command` (required): The Azure CLI command to execute (without 'az' prefix)

**Examples:**

```bash
# Resource group operations (specify subscription)
azure_cli command="group list --subscription 'My Subscription'"
azure_cli command="group create --name myResourceGroup --location eastus --subscription 'My Subscription'"
azure_cli command="group show --name myResourceGroup --subscription 'My Subscription'"
azure_cli command="group delete --name myResourceGroup --yes --no-wait --subscription 'My Subscription'"

# Virtual machine operations
azure_cli command="vm list --subscription 'My Subscription'"
azure_cli command="vm create --resource-group myResourceGroup --name myVM --image UbuntuLTS --size Standard_B1ls --subscription 'My Subscription'"
azure_cli command="vm show --resource-group myResourceGroup --name myVM --subscription 'My Subscription'"
azure_cli command="vm start --resource-group myResourceGroup --name myVM --subscription 'My Subscription'"

# Storage account operations
azure_cli command="storage account list --subscription 'My Subscription'"
azure_cli command="storage account create --name mystorageaccount --resource-group myResourceGroup --location eastus --sku Standard_LRS --subscription 'My Subscription'"
azure_cli command="storage account show --name mystorageaccount --resource-group myResourceGroup --subscription 'My Subscription'"

# Application Insights operations
azure_cli command="monitor app-insights component show --app myApp --resource-group myResourceGroup --subscription 'My Subscription'"
azure_cli command="monitor app-insights query --app myApp --analytics-query \"requests | limit 10\" --subscription 'My Subscription'"
azure_cli command="monitor app-insights events show --app myApp --type requests --start-time \"2023-01-01T00:00:00Z\" --end-time \"2023-01-02T00:00:00Z\" --subscription 'My Subscription'"

# Web app operations
azure_cli command="webapp list --subscription 'My Subscription'"
azure_cli command="webapp create --resource-group myResourceGroup --plan myAppServicePlan --name myWebApp --subscription 'My Subscription'"
azure_cli command="webapp show --name myWebApp --resource-group myResourceGroup --subscription 'My Subscription'"

# Advanced operations with JSON output
azure_cli command="vm list --output json --subscription 'My Subscription'"
azure_cli command="group list --query \"[?location=='eastus']\" --output table --subscription 'My Subscription'"
```

## Common Use Cases

### Getting Started
```bash
# First, list available subscriptions
azure_subscriptions_list

# Then use commands with the subscription you want
azure_cli command="group list --subscription 'My Subscription Name'"
```

### Resource Management
```bash
# List all resource groups in a subscription
azure_cli command="group list --subscription 'My Subscription'"

# Create a resource group
azure_cli command="group create --name myResourceGroup --location eastus --subscription 'My Subscription'"

# List resources in a resource group
azure_cli command="resource list --resource-group myResourceGroup --subscription 'My Subscription'"

# Get resource group information
azure_cli command="group show --name myResourceGroup --subscription 'My Subscription'"
```

### Virtual Machine Management
```bash
# List virtual machines in a subscription
azure_cli command="vm list --output table --subscription 'My Subscription'"

# Create a virtual machine
azure_cli command="vm create --resource-group myResourceGroup --name myVM --image UbuntuLTS --admin-username azureuser --generate-ssh-keys --subscription 'My Subscription'"

# Start/stop virtual machines
azure_cli command="vm start --resource-group myResourceGroup --name myVM --subscription 'My Subscription'"
azure_cli command="vm stop --resource-group myResourceGroup --name myVM --subscription 'My Subscription'"

# Get VM status
azure_cli command="vm get-instance-view --resource-group myResourceGroup --name myVM --subscription 'My Subscription'"
```

### Application Insights Log Retrieval
```bash
# Query Application Insights logs
azure_cli command="monitor app-insights query --app myAppInsights --analytics-query \"requests | where timestamp >= ago(1h) | limit 100\" --subscription 'My Subscription'"

# Get specific event types
azure_cli command="monitor app-insights events show --app myAppInsights --type requests --start-time \"2023-12-01T00:00:00Z\" --end-time \"2023-12-02T00:00:00Z\" --subscription 'My Subscription'"

# Query with filters
azure_cli command="monitor app-insights query --app myAppInsights --analytics-query \"requests | where name contains 'api' and resultCode != '200' | where timestamp between(ago(24h) .. ago(1h))\" --subscription 'My Subscription'"

# Get metrics
azure_cli command="monitor app-insights metrics show --app myAppInsights --metric requests/count --start-time 2023-12-01T00:00:00Z --end-time 2023-12-02T00:00:00Z --subscription 'My Subscription'"
```

### Storage Operations
```bash
# List storage accounts
azure_cli command="storage account list --output table --subscription 'My Subscription'"

# Create storage account
azure_cli command="storage account create --name mystorageaccount --resource-group myResourceGroup --location eastus --sku Standard_LRS --subscription 'My Subscription'"

# List containers
azure_cli command="storage container list --account-name mystorageaccount --subscription 'My Subscription'"

# Upload/download blobs
azure_cli command="storage blob upload --account-name mystorageaccount --container-name mycontainer --name myblob --file ./localfile.txt --subscription 'My Subscription'"
```

### Web App Management
```bash
# List web apps
azure_cli command="webapp list --output table --subscription 'My Subscription'"

# Create web app
azure_cli command="webapp create --resource-group myResourceGroup --plan myAppServicePlan --name myWebApp --runtime \"PYTHON|3.9\" --subscription 'My Subscription'"

# Get web app logs
azure_cli command="webapp log tail --name myWebApp --resource-group myResourceGroup --subscription 'My Subscription'"

# Configure app settings
azure_cli command="webapp config appsettings set --name myWebApp --resource-group myResourceGroup --settings CUSTOM_SETTING=value --subscription 'My Subscription'"
```

### Advanced Querying
```bash
# Use JMESPath queries
azure_cli command="vm list --query \"[?powerState=='VM running'].{Name:name, ResourceGroup:resourceGroup, Location:location}\" --output table --subscription 'My Subscription'"

# Filter by tags
azure_cli command="resource list --tag environment=production --output table --subscription 'My Subscription'"

# Get specific properties
azure_cli command="webapp list --query \"[].{Name:name, State:state, Location:location}\" --output json --subscription 'My Subscription'"
```

## Environment Variables

The following environment variables are required:

- `AZURE_CLIENT_ID`: Azure service principal client ID
- `AZURE_CLIENT_SECRET`: Azure service principal client secret  
- `AZURE_TENANT_ID`: Azure tenant ID

Optional environment variables:
- `AZURE_RESOURCE_GROUP`: Default resource group for operations
- `AZURE_LOCATION`: Default location for resource creation

## Authentication

To use this tool, you need to set up Azure authentication using a service principal:

1. Create a service principal:
   ```bash
   az ad sp create-for-rbac --name "kubiya-service-principal" --role contributor --scopes /subscriptions/{subscription-id}
   ```

2. The command will return credentials that you should set as environment variables:
   - `AZURE_CLIENT_ID`: The `appId` from the output
   - `AZURE_CLIENT_SECRET`: The `password` from the output  
   - `AZURE_TENANT_ID`: The `tenant` from the output

3. Grant appropriate permissions to the service principal based on your needs

## Workflow

1. **List Subscriptions**: Use `azure_subscriptions_list` to see available subscriptions
2. **Execute Commands**: Use `azure_cli` with `--subscription` parameter to specify which subscription to use
3. **Dynamic Selection**: Switch between subscriptions as needed for different operations

## Installation

```bash
pip install -r requirements.txt
pip install -e .
```

## Docker Usage

```bash
# Build the Docker image (uses official Azure CLI image as base)
docker build -t azure-cli-tools .

# Run with environment variables
docker run -e AZURE_CLIENT_ID=your_client_id -e AZURE_CLIENT_SECRET=your_secret -e AZURE_TENANT_ID=your_tenant azure-cli-tools
```

**Note**: This tool uses the official Microsoft Azure CLI Docker image (`mcr.microsoft.com/azure-cli:latest`) as its base, which provides:
- ✅ Pre-installed Azure CLI (no installation time)
- ✅ Always up-to-date with latest Azure CLI version
- ✅ Optimized and maintained by Microsoft
- ✅ Faster startup times
- ✅ Smaller attack surface

## Error Handling

The tool includes comprehensive error handling:
- Environment variable validation
- Command argument validation
- Azure CLI error responses
- Network connectivity issues
- Authentication failures
- Exit code propagation

## AI Usage Tips

When using this tool with AI:

1. **Start with subscriptions**: Always use `azure_subscriptions_list` first to see available subscriptions
2. **Pass complete commands**: Include all necessary flags and arguments
3. **Use proper quoting**: Quote strings with spaces: `--name "My Resource"`
4. **Specify subscriptions**: Always use `--subscription` parameter to be explicit
5. **Use JSON output**: Add `--output json` for structured data when parsing is needed
6. **Use queries**: Leverage JMESPath with `--query` for filtering results
7. **Check Azure CLI docs**: The tool supports all official `az` commands

## Supported Commands

This tool supports all Azure CLI commands including:
- `group` - Resource group operations
- `vm` - Virtual machine management
- `storage` - Storage account and blob operations
- `webapp` - Web app management
- `functionapp` - Function app operations
- `keyvault` - Key vault management
- `network` - Network operations
- `monitor` - Monitoring and Application Insights
- `sql` - SQL database operations
- `cosmosdb` - Cosmos DB operations
- `containerapp` - Container app management
- `aks` - Azure Kubernetes Service
- `acr` - Azure Container Registry
- And many more...

## Security Notes

- Store your Azure credentials securely
- Use environment variables, not hardcoded values
- Follow the principle of least privilege when assigning roles
- Regularly rotate your service principal credentials
- Be careful with destructive operations
- Use `--dry-run` flag when available for testing

## Application Insights Specific Examples

### Log Queries
```bash
# Get recent requests
azure_cli command="monitor app-insights query --app myApp --analytics-query \"requests | where timestamp >= ago(1h) | order by timestamp desc\" --subscription 'My Subscription'"

# Find errors in specific time range
azure_cli command="monitor app-insights query --app myApp --analytics-query \"requests | where timestamp between(datetime('2023-12-01T10:00:00Z') .. datetime('2023-12-01T11:00:00Z')) and resultCode >= '400'\" --subscription 'My Subscription'"

# Get performance data
azure_cli command="monitor app-insights query --app myApp --analytics-query \"requests | summarize avg(duration) by bin(timestamp, 5m) | order by timestamp desc\" --subscription 'My Subscription'"

# Custom events
azure_cli command="monitor app-insights query --app myApp --analytics-query \"customEvents | where name == 'UserLogin' | where timestamp >= ago(24h)\" --subscription 'My Subscription'"
```

## Support

For issues, questions, or contributions, please refer to the Kubiya documentation or contact the development team.

For Azure CLI specific help, run:
```bash
azure_cli command="help"
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 