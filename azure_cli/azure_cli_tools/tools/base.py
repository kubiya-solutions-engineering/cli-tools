from typing import List, Optional, Dict, Any
from kubiya_sdk.tools import Tool, Arg, FileSpec

AZURE_CLI_ICON_URL = "https://docs.microsoft.com/en-us/media/logos/logo_azure.svg"

DEFAULT_MERMAID = """
```mermaid
classDiagram
    class Tool {
        <<interface>>
        +get_args()
        +get_content()
        +get_image()
    }
    class AzureCLITool {
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
    Tool <|-- AzureCLITool
```
"""

class AzureCLITool(Tool):
    """Base class for all Azure CLI tools."""
    
    name: str
    description: str
    content: str = ""
    args: List[Arg] = []
    image: str = "mcr.microsoft.com/azure-cli:latest"
    icon_url: str = AZURE_CLI_ICON_URL
    type: str = "docker"
    mermaid: str = DEFAULT_MERMAID
    
    def __init__(self, name, description, content, args=None, image="mcr.microsoft.com/azure-cli:latest"):
        content = content
        
        super().__init__(
            name=name,
            description=description,
            content=content,
            args=args or [],
            image=image,
            icon_url=AZURE_CLI_ICON_URL,
            type="docker",
            secrets=["AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET", "AZURE_TENANT_ID"],
            env=[]
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