from typing import List, Optional, Dict, Any
from kubiya_sdk.tools import Tool, Arg, FileSpec
import tempfile
import os

DATADOG_CLI_ICON_URL = "https://cdn.worldvectorlogo.com/logos/datadog.svg"

DEFAULT_MERMAID = """
```mermaid
classDiagram
    class Tool {
        <<interface>>
        +get_args()
        +get_content()
        +get_image()
    }
    class DatadogCLITool {
        -content: str
        -args: List[Arg]
        -image: str
        +__init__(name, description, content, args, image)
        +get_args()
        +get_content()
        +get_image()
        +get_file_specs()
        +validate_args(args)
        +get_error_message(args)
        +get_environment()
    }
    Tool <|-- DatadogCLITool
```
"""

class DatadogCLITool(Tool):
    """Base class for all Datadog CLI tools."""
    
    def __init__(self, name, description, content, args=None, image="datadog/cli:latest"):
        # Create the .dogrc configuration file content
        dogrc_content = """[Connection]
apikey = ${DD_API_KEY}
appkey = ${DD_APP_KEY}
api_host = https://api.${DD_SITE}
"""
        
        # Create a temporary file for the .dogrc content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dogrc', delete=False) as f:
            f.write(dogrc_content)
            dogrc_path = f.name
        
        # Define file specifications
        file_specs = [
            FileSpec(
                source=dogrc_path,
                destination="/root/.dogrc"
            )
        ]
        
        # Add configuration setup to content
        setup_config = """
# Setup Datadog configuration
if [ -f /root/.dogrc ]; then
    echo "✅ Datadog configuration file found"
else
    echo "❌ Error: Datadog configuration file not found"
    exit 1
fi

# Validate authentication environment variables
if [ -z "$DD_API_KEY" ]; then
    echo "❌ Error: DD_API_KEY environment variable is not set"
    echo ""
    echo "💡 Hint: Set your Datadog API key:"
    echo "  export DD_API_KEY='your-api-key-here'"
    echo ""
    echo "You can find your API key in Datadog:"
    echo "  Settings → API Keys → Create API Key"
    exit 1
fi

if [ -z "$DD_APP_KEY" ]; then
    echo "❌ Error: DD_APP_KEY environment variable is not set"
    echo ""
    echo "💡 Hint: Set your Datadog Application key:"
    echo "  export DD_APP_KEY='your-app-key-here'"
    echo ""
    echo "You can find your Application key in Datadog:"
    echo "  Settings → Application Keys → Create Application Key"
    exit 1
fi

if [ -z "$DD_SITE" ]; then
    echo "❌ Error: DD_SITE environment variable is not set"
    echo ""
    echo "💡 Hint: Set your Datadog site:"
    echo "  export DD_SITE='datadoghq.com'  # US site"
    echo "  export DD_SITE='datadoghq.eu'   # EU site"
    echo "  export DD_SITE='us3.datadoghq.com'  # US3 site"
    exit 1
fi
"""
        full_content = f"{setup_config}\n{content}"
        
        super().__init__(
            name=name,
            description=description,
            content=full_content,
            args=args or [],
            image=image,
            icon_url=DATADOG_CLI_ICON_URL,
            type="docker",
            secrets=["DD_API_KEY", "DD_APP_KEY"],
            env=["DD_SITE"],
            with_files=file_specs,
            mermaid=DEFAULT_MERMAID
        )

    def get_args(self) -> List[Arg]:
        """Return the tool's arguments."""
        return self.args

    def get_content(self) -> str:
        """Return the tool's shell script content."""
        return self.content

    def get_image(self) -> str:
        """Return the Docker image to use."""
        return self.image

    def validate_args(self, args: Dict[str, Any]) -> bool:
        """Validate the provided arguments."""
        required_args = [arg.name for arg in self.args if arg.required]
        return all(arg in args and args[arg] for arg in required_args)

    def get_error_message(self, args: Dict[str, Any]) -> Optional[str]:
        """Return error message if arguments are invalid."""
        missing_args = []
        for arg in self.args:
            if arg.required and (arg.name not in args or not args[arg.name]):
                missing_args.append(arg.name)
        
        if missing_args:
            return f"Missing required arguments: {', '.join(missing_args)}"
        return None 