"""
Test configuration and fixtures for observe_cli_tools tests.
"""
import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add the observe_cli directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "observe_cli"))

from observe_cli_tools.tools.base import ObserveCLITool
from observe_cli_tools.tools.cli import CLITools


@pytest.fixture
def mock_env():
    """Mock environment variables for testing."""
    return {
        'OBSERVE_API_KEYS': '{"NA": "test_na_key_123456789", "EU": "test_eu_key_987654321"}',
        'OBSERVE_CUSTOMER_ID': 'test_customer_123',
        'OBSERVE_DATASET_IDS': '41000001,41000002'
    }


@pytest.fixture
def sample_opal_response():
    """Sample OPAL query response for testing."""
    return {
        "data": [
            {
                "timestamp": "2024-01-15T10:30:00Z",
                "level": "ERROR",
                "message": "Database connection failed",
                "applicationName": "web-service",
                "statusCode": 500,
                "userId": "user123",
                "endpoint": "/api/users"
            },
            {
                "timestamp": "2024-01-15T10:31:00Z", 
                "level": "WARN",
                "message": "High memory usage detected",
                "applicationName": "worker-service",
                "statusCode": 200,
                "userId": "user456",
                "endpoint": "/api/jobs"
            }
        ],
        "metadata": {
            "recordCount": 2,
            "queryTime": "1.234s"
        }
    }


@pytest.fixture
def sample_large_response():
    """Sample large response for pagination testing."""
    data = []
    for i in range(100):
        data.append({
            "timestamp": f"2024-01-15T10:{30+i:02d}:00Z",
            "level": "INFO" if i % 2 == 0 else "ERROR",
            "message": f"Log message {i} with some content that makes it longer",
            "applicationName": "test-service",
            "statusCode": 200 if i % 2 == 0 else 500,
            "userId": f"user{i}",
            "endpoint": f"/api/test/{i}"
        })
    
    return {
        "data": data,
        "metadata": {
            "recordCount": 100,
            "queryTime": "2.456s"
        }
    }


@pytest.fixture
def cli_tools():
    """Create CLITools instance for testing."""
    with patch('observe_cli_tools.tools.cli.tool_registry'):
        return CLITools()


@pytest.fixture
def opal_query_tool(cli_tools):
    """Get the OPAL query tool for testing."""
    return cli_tools.execute_opal_query()


@pytest.fixture
def mock_curl_success():
    """Mock successful curl response."""
    def _mock_curl(return_data):
        def side_effect(*args, **kwargs):
            return (json.dumps(return_data), 0)  # (stdout, returncode)
        return side_effect
    return _mock_curl


@pytest.fixture
def mock_curl_failure():
    """Mock failed curl response."""
    def _mock_curl(error_code=1, error_msg="Connection failed"):
        def side_effect(*args, **kwargs):
            return (error_msg, error_code)  # (stdout, returncode)
        return side_effect
    return _mock_curl


@pytest.fixture
def temp_workspace(tmp_path):
    """Create temporary workspace directory for testing."""
    workspace = tmp_path / "observe-data"
    workspace.mkdir()
    
    # Create subdirectories
    (workspace / "cache").mkdir()
    (workspace / "templates").mkdir() 
    (workspace / "metrics").mkdir()
    
    return workspace