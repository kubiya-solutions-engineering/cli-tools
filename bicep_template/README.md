# Bicep Template Tools

A flexible Bicep template processing tool for Kubiya, providing AI-controlled access to Bicep template validation, building, and deployment capabilities.

## Overview

This package provides a single, flexible tool that processes Bicep templates for Azure infrastructure deployment. The tool can handle Bicep template files, URLs, or raw template content, allowing AI agents to validate and build Bicep templates through the Kubiya platform.

## Features

- **Flexible Input**: Accept Bicep templates as file paths, URLs, or raw content
- **Template Validation**: Validate Bicep template syntax and structure
- **ARM Template Generation**: Build Bicep templates into ARM templates
- **Azure Integration**: Seamless Azure CLI integration for authentication
- **AI-Friendly**: Simple interface for AI agents to process Azure infrastructure as code
- **Docker-based**: Consistent execution environment with all required tools

## Available Tool

### `bicep_template`
Process Bicep templates by validating, building, and preparing them for deployment.

**Parameters:**
- `template` (required): The Bicep template to process. Can be:
  1. File path to a `.bicep` file
  2. URL to a Bicep template (e.g., from GitHub)
  3. Raw Bicep template content as a string

**Examples:**

```bash
# Process a local Bicep file
bicep_template template="./infrastructure/main.bicep"

# Process a Bicep template from a URL
bicep_template template="https://raw.githubusercontent.com/Azure/azure-quickstart-templates/master/quickstarts/microsoft.storage/storage-account-create/main.bicep"

# Process raw Bicep template content
bicep_template template="resource storageAccount 'Microsoft.Storage/storageAccounts@2021-04-01' = {
  name: 'mystorageaccount'
  location: resourceGroup().location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
}"
```

## What the Tool Does

1. **Authentication**: Authenticates with Azure using service principal credentials
2. **Input Processing**: Determines if the input is a file path, URL, or raw content
3. **Template Validation**: Validates the Bicep template syntax
4. **ARM Generation**: Builds the Bicep template into an ARM template
5. **Output**: Provides the generated ARM template and deployment guidance

## Prerequisites

### Environment Variables
The following Azure service principal credentials are required:

- `AZURE_CLIENT_ID`: Azure Active Directory application (client) ID
- `AZURE_CLIENT_SECRET`: Azure Active Directory application client secret
- `AZURE_TENANT_ID`: Azure Active Directory tenant ID

### Setting up Azure Service Principal

1. Create a service principal:
```bash
az ad sp create-for-rbac --name "bicep-tool-sp" --role contributor
```

2. Note the output values:
```json
{
  "appId": "your-client-id",
  "password": "your-client-secret",
  "tenant": "your-tenant-id"
}
```

3. Set the environment variables:
```bash
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_TENANT_ID="your-tenant-id"
```

## Installation

### Docker Installation (Recommended)

Build the Docker image:
```bash
cd bicep_template
docker build -t bicep-template-tools .
```

### Local Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install Azure CLI:
```bash
# On Ubuntu/Debian
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# On macOS
brew install azure-cli

# On Windows
# Download and run the MSI from https://aka.ms/installazurecliwindows
```

3. Install Bicep CLI:
```bash
# On Linux
curl -Lo bicep https://github.com/Azure/bicep/releases/latest/download/bicep-linux-x64
chmod +x ./bicep
sudo mv ./bicep /usr/local/bin/bicep

# On macOS
brew install bicep

# On Windows
winget install -e --id Microsoft.Bicep
```

4. Install the package:
```bash
pip install -e .
```

## Usage Examples

### Basic Storage Account Template

```bash
bicep_template template="
param storageAccountName string = 'mystorageaccount'
param location string = resourceGroup().location

resource storageAccount 'Microsoft.Storage/storageAccounts@2021-04-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
  }
}

output storageAccountId string = storageAccount.id
"
```

### Virtual Machine Template from URL

```bash
bicep_template template="https://raw.githubusercontent.com/Azure/azure-quickstart-templates/master/quickstarts/microsoft.compute/vm-simple-linux/main.bicep"
```

### Local Template File

```bash
bicep_template template="./templates/webapp.bicep"
```

## Tool Output

The tool provides:

1. **Validation Results**: Confirms if the Bicep template is syntactically correct
2. **Generated ARM Template**: JSON representation of the compiled template
3. **Deployment Guidance**: Instructions for deploying the template using Azure CLI

## Error Handling

The tool handles various error scenarios:

- **Missing Authentication**: Validates Azure service principal credentials
- **Invalid Templates**: Catches Bicep syntax errors and compilation issues
- **Network Issues**: Handles URL download failures gracefully
- **File Access**: Validates file paths and permissions

## Integration with Kubiya

This tool integrates seamlessly with the Kubiya platform, allowing AI agents to:

- Validate infrastructure-as-code templates
- Generate deployment-ready ARM templates
- Assist with Azure infrastructure planning
- Provide deployment guidance and best practices

## Development

### Project Structure

```
bicep_template/
├── README.md
├── setup.py
├── requirements.txt
├── Dockerfile
└── bicep_template_tools/
    ├── __init__.py
    └── tools/
        ├── __init__.py
        ├── base.py
        └── cli.py
```

### Running Tests

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:

1. Check the GitHub issues page
2. Review Azure Bicep documentation: https://docs.microsoft.com/en-us/azure/azure-resource-manager/bicep/
3. Consult Azure CLI documentation: https://docs.microsoft.com/en-us/cli/azure/

## Changelog

### v0.1.0
- Initial release
- Basic Bicep template processing
- ARM template generation
- Azure CLI integration 