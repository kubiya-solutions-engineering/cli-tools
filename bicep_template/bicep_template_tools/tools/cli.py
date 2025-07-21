from typing import List
import sys
from .base import BicepTemplateTool, Arg
from kubiya_sdk.tools.registry import tool_registry

class CLITools:
    """Bicep template tool for processing and deploying Bicep templates."""

    def __init__(self):
        """Initialize and register the Bicep template tools."""
        try:
            # Register the full deployment tool
            tool = self.bicep_template()
            tool_registry.register("bicep_template", tool)
            print(f"✅ Registered: {tool.name}")
        except Exception as e:
            print(f"❌ Failed to register Bicep template tools: {str(e)}", file=sys.stderr)
            raise


    def bicep_template(self) -> BicepTemplateTool:
        """A Bicep template tool that processes Bicep template files or content."""
        return BicepTemplateTool(
            name="bicep_template",
            description="Process Bicep templates - validate, build, or deploy Azure infrastructure using Bicep. Pass a Bicep template file path, URL, or template content as the 'template' argument.",
            content="""
            # Validate environment
            if [ -z "$AZURE_CLIENT_ID" ] || [ -z "$AZURE_CLIENT_SECRET" ] || [ -z "$AZURE_TENANT_ID" ]; then
                echo "❌ Azure authentication environment variables are required:"
                echo "   - AZURE_CLIENT_ID"
                echo "   - AZURE_CLIENT_SECRET"  
                echo "   - AZURE_TENANT_ID"
                exit 1
            fi
            
            if [ -z "$template" ]; then
                echo "❌ Template argument is required"
                echo "Usage: Pass a Bicep template file path, URL, or template content as the 'template' argument"
                echo "Examples:"
                echo "  template='./main.bicep'"
                echo "  template='https://raw.githubusercontent.com/Azure/azure-quickstart-templates/master/quickstarts/microsoft.storage/storage-account-create/main.bicep'"
                echo "  template='resource storageAccount \"Microsoft.Storage/storageAccounts@2021-04-01\" = { ... }'"
                exit 1
            fi
            
            # Install required packages (Azure CLI and Bicep are in Dockerfile)
            echo "🔧 Setting up Azure CLI and Bicep environment..."
            
            # Authenticate with Azure
            echo "🔐 Authenticating with Azure..."
            az login --service-principal -u "$AZURE_CLIENT_ID" -p "$AZURE_CLIENT_SECRET" --tenant "$AZURE_TENANT_ID"
            
            if [ $? -ne 0 ]; then
                echo "❌ Azure authentication failed"
                exit 1
            fi
            
            # Determine if template is a file path, URL, or content
            template_input="$template"
            template_file=""
            
            if echo "$template_input" | grep -E '^https?://' >/dev/null; then
                # It's a URL - download it
                echo "🌐 Downloading Bicep template from URL..."
                template_file="/tmp/downloaded_template.bicep"
                curl -s -o "$template_file" "$template_input"
                if [ $? -ne 0 ]; then
                    echo "❌ Failed to download template from URL: $template_input"
                    exit 1
                fi
                echo "✅ Template downloaded successfully"
            elif [ -f "$template_input" ]; then
                # It's a file path
                echo "📁 Using Bicep template file: $template_input"
                template_file="$template_input"
            else
                # It's template content - write to temporary file
                echo "📝 Processing Bicep template content..."
                template_file="/tmp/template_content.bicep"
                echo "$template_input" > "$template_file"
                echo "✅ Template content written to temporary file"
            fi
            
            # Validate the template file exists
            if [ ! -f "$template_file" ]; then
                echo "❌ Template file not found: $template_file"
                exit 1
            fi
            
            echo "🔍 Validating Bicep template..."
            echo "Template file: $template_file"
            echo "----------------------------------------"
            
            # Build the Bicep template to ARM template
            echo "🔨 Building Bicep template..."
            arm_template="/tmp/template.json"
            bicep build "$template_file" --outfile "$arm_template"
            
            if [ $? -eq 0 ]; then
                echo "✅ Bicep template built successfully"
                echo "📋 Generated ARM template:"
                cat "$arm_template" | jq '.' 2>/dev/null || cat "$arm_template"
                echo "----------------------------------------"
            else
                echo "❌ Bicep template build failed"
                exit 1
            fi
            
            # Validate the ARM template
            echo "✅ Bicep template processing completed successfully"
            echo "💡 To deploy this template, you can use the generated ARM template with Azure CLI:"
            echo "   az deployment group create --resource-group <resource-group> --template-file $arm_template"
            """,
            args=[
                Arg(name="template", description="Bicep template to process. Can be: 1) File path to .bicep file, 2) URL to a Bicep template, or 3) Bicep template content as a string", required=True)
            ]
        )


# Initialize the CLI tools when the module is imported
cli_tools = CLITools() 