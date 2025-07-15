# Python Script Runner Tools

A Docker-based Python script runner that can execute any Python script with pre-installed libraries.

## Structure

This package follows the Kubiya tools pattern:
```
python_script_runner/
├── python_script_runner_tools/
│   ├── tools/
│   │   └── script_runner.py
│   ├── __init__.py
│   └── __main__.py
├── requirements.txt
├── setup.py
├── Dockerfile
└── README.md
```

## Pre-installed Libraries

This container comes with the following Python libraries pre-installed:
- **pandas**: Data manipulation and analysis
- **openpyxl**: Excel file reading and writing
- **lxml**: XML and HTML processing

## Usage

### Building the Docker Image

```bash
docker build -t python-script-runner-tools .
```

### Running a Python Script

1. Place your Python script in the same directory as the Dockerfile
2. Run the container with your script:

```bash
docker run -v $(pwd):/app python-script-runner-tools python -m python_script_runner_tools your_script.py
```

Or to run a script directly:

```bash
docker run -v $(pwd):/app python-script-runner-tools python your_script.py
```

### Example

Create a sample script `test_script.py`:

```python
import pandas as pd
import openpyxl
import lxml

print("Testing libraries...")
print(f"Pandas version: {pd.__version__}")
print(f"Openpyxl version: {openpyxl.__version__}")
print(f"Lxml version: {lxml.__version__}")

# Create a simple DataFrame
df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
print("\nDataFrame:")
print(df)
```

Then run it:

```bash
docker run -v $(pwd):/app python-script-runner-tools python test_script.py
```

## Features

- Python 3.11 slim base image
- Pre-installed data processing libraries
- Volume mounting for easy script execution
- Error handling and output capture
- Follows Kubiya tools structure pattern 