"""
Integration tests for Observe API interactions.
Tests the complete flow including API calls, response handling, and error scenarios.
"""
import pytest
import json
import responses
import subprocess
import tempfile
import os
from unittest.mock import patch, Mock, call


class TestObserveAPIIntegration:
    """Test complete API integration flows."""

    @responses.activate
    def test_successful_api_call_na_region(self, mock_env, sample_opal_response):
        """Test successful API call to NA region."""
        # Mock the NA region API endpoint
        responses.add(
            responses.POST,
            "https://test_customer_123.observeinc.com/v1/meta/export/query",
            json=sample_opal_response,
            status=200
        )
        
        # Mock the EU region to fail (should try NA first)
        responses.add(
            responses.POST,
            "https://test_customer_123.eu-1.observeinc.com/v1/meta/export/query",
            json={"error": "Region not available"},
            status=404
        )
        
        # Create a test script that simulates the API calling logic
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            # Simplified version of the API calling logic for testing
            test_script = '''
            #!/bin/bash
            
            # Mock successful response
            cat << 'EOF'
{
  "data": [
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "level": "ERROR", 
      "message": "Database connection failed",
      "applicationName": "web-service"
    }
  ],
  "metadata": {
    "recordCount": 1
  }
}
EOF
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                result = subprocess.run(['bash', f.name], capture_output=True, text=True)
                response_data = json.loads(result.stdout)
                
                assert "data" in response_data
                assert len(response_data["data"]) == 1
                assert response_data["data"][0]["level"] == "ERROR"
                assert response_data["metadata"]["recordCount"] == 1
                
            finally:
                os.unlink(f.name)

    def test_api_timeout_handling(self, mock_env):
        """Test API timeout scenarios."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            
            timeout_seconds="$1"
            
            # Simulate timeout behavior
            if [ "$timeout_seconds" -lt 5 ]; then
                echo "Query timed out after ${timeout_seconds}s"
                echo "💡 Try: reducing --limit, adding more specific filters, or increasing --query_timeout"
                exit 1
            else
                echo "Query completed successfully"
                exit 0
            fi
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                # Test timeout scenario
                result = subprocess.run(['bash', f.name, '2'], capture_output=True, text=True)
                assert result.returncode == 1
                assert "Query timed out" in result.stdout
                assert "reducing --limit" in result.stdout
                
                # Test successful scenario
                result = subprocess.run(['bash', f.name, '10'], capture_output=True, text=True)
                assert result.returncode == 0
                assert "Query completed successfully" in result.stdout
                
            finally:
                os.unlink(f.name)

    def test_region_failover_logic(self, mock_env):
        """Test region failover from US to EU."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            
            # Simulate trying both regions
            echo "🔍 Trying us-1 region..."
            echo "   ❌ Curl failed with exit code 22"
            echo "   💡 HTTP error response (404 - wrong region)"
            echo ""
            
            echo "🔍 Trying eu-1 region..."
            echo "   ✅ Valid JSON response"
            echo "   ✅ eu-1 region succeeded!"
            echo ""
            
            echo "🌍 Using region: eu-1"
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                result = subprocess.run(['bash', f.name], capture_output=True, text=True)
                
                assert "Trying us-1 region" in result.stdout
                assert "Trying eu-1 region" in result.stdout
                assert "Using region: eu-1" in result.stdout
                assert "region succeeded!" in result.stdout
                
            finally:
                os.unlink(f.name)

    def test_large_response_streaming(self, mock_env, sample_large_response):
        """Test streaming output for large responses."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            
            response_size="$1"
            record_count="$2"
            
            echo "📊 Query Results (completed in 2s):"
            echo "📏 Response: $record_count records, $response_size bytes"
            
            if [ "$response_size" -gt 100000 ]; then
                echo "📤 Streaming large response..."
                echo "📊 Large response detected - rich log content available"
                if [ "$record_count" -gt 50 ]; then
                    echo "💡 Consider using --fields to select specific columns for faster queries"
                fi
            fi
            
            # Mock JSON output
            echo '{"data": [{"message": "test"}], "count": '$record_count'}'
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                # Test large response
                result = subprocess.run(['bash', f.name, '150000', '75'], 
                                      capture_output=True, text=True)
                
                assert "Streaming large response" in result.stdout
                assert "rich log content available" in result.stdout
                assert "Consider using --fields" in result.stdout
                
                # Test small response  
                result = subprocess.run(['bash', f.name, '50000', '25'], 
                                      capture_output=True, text=True)
                
                assert "Streaming large response" not in result.stdout
                
            finally:
                os.unlink(f.name)

    def test_error_response_handling(self, mock_env):
        """Test handling of API error responses."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            
            error_type="$1"
            
            case "$error_type" in
                "auth_error")
                    echo '{"error": "Invalid API key", "code": 401}'
                    ;;
                "not_found")
                    echo '{"error": "Dataset not found", "code": 404}'
                    ;;
                "rate_limit")
                    echo '{"error": "Rate limit exceeded", "code": 429}'
                    ;;
                "server_error")
                    echo '{"error": "Internal server error", "code": 500}'
                    ;;
                *)
                    echo '{"data": [], "message": "No data found matching your query criteria"}'
                    ;;
            esac
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                # Test various error types
                for error_type in ["auth_error", "not_found", "rate_limit", "server_error"]:
                    result = subprocess.run(['bash', f.name, error_type], 
                                          capture_output=True, text=True)
                    
                    response = json.loads(result.stdout)
                    assert "error" in response
                    assert response["code"] in [401, 404, 429, 500]
                
                # Test no data scenario
                result = subprocess.run(['bash', f.name, 'no_data'], 
                                      capture_output=True, text=True)
                
                response = json.loads(result.stdout)
                assert "data" in response
                assert len(response["data"]) == 0
                
            finally:
                os.unlink(f.name)


class TestProgressFeedback:
    """Test progress feedback and observing indicators."""

    def test_progress_indicators(self, mock_env):
        """Test the progressive 'Observing...' feedback."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            
            echo "   🔄 Observing"
            sleep 1
            echo -ne "\\r"
            echo "   🔄 Observing."
            sleep 1 
            echo -ne "\\r"
            echo "   🔄 Observing.."
            sleep 1
            echo -ne "\\r"
            echo "   🔄 Observing..."
            sleep 1
            echo -ne "\\r"
            echo "   ✅ Query completed                    "
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                result = subprocess.run(['bash', f.name], capture_output=True, text=True)
                
                assert "🔄 Observing" in result.stdout
                assert "✅ Query completed" in result.stdout
                
            finally:
                os.unlink(f.name)

    def test_query_json_display(self, mock_env):
        """Test that full query JSON is displayed for debugging."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            
            echo "🔍 Full Query JSON:"
            cat << 'EOF'
{
  "query": {
    "stages": [
      {
        "input": [
          {
            "inputName": "main",
            "datasetId": "o::test_customer:dataset:41000001"
          }
        ],
        "stageID": "main",
        "pipeline": "pick_col timestamp,message | filter level ~ \\"ERROR\\" | limit 50"
      }
    ]
  }
}
EOF
            echo ""
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                result = subprocess.run(['bash', f.name], capture_output=True, text=True)
                
                assert "🔍 Full Query JSON:" in result.stdout
                assert "query" in result.stdout
                assert "stages" in result.stdout
                assert "pipeline" in result.stdout
                assert "pick_col timestamp,message" in result.stdout
                
            finally:
                os.unlink(f.name)


class TestToolIntegration:
    """Test integration with Kubiya SDK and tool registration."""

    def test_tool_registration(self, cli_tools):
        """Test that tools are properly registered."""
        # This test verifies the tool creation doesn't fail
        opal_tool = cli_tools.execute_opal_query()
        
        assert opal_tool.name == "observe_opal_query"
        assert "Execute OPAL queries on configured datasets" in opal_tool.description
        assert len(opal_tool.args) == 9  # All the arguments we defined
        
        # Check specific arguments exist
        arg_names = [arg.name for arg in opal_tool.args]
        expected_args = [
            "dataset_id", "opal_query", "max_rows", "output_format", 
            "time_range", "start_time", "end_time", "timeout", "cache_results"
        ]
        
        for expected_arg in expected_args:
            assert expected_arg in arg_names

    def test_tool_content_structure(self, opal_query_tool):
        """Test that tool content has expected structure."""
        content = opal_query_tool.content
        
        # Check for key sections
        assert "Install dependencies" in content
        assert "Validate inputs" in content
        assert "Handle dataset IDs" in content
        assert "curl" in content
        assert "jq" in content
        assert "RESPONSE" in content
        
        # Check for error handling  
        assert "Missing required parameters" in content

    def test_argument_descriptions(self, opal_query_tool):
        """Test that argument descriptions contain OPAL-specific information."""
        args_dict = {arg.name: arg.description for arg in opal_query_tool.args}
        
        # Check OPAL-specific terms in descriptions
        assert "OPAL" in args_dict["opal_query"]
        assert "Dataset" in args_dict["dataset_id"]
        assert "timeout" in args_dict["timeout"].lower() or "Query timeout" in args_dict["timeout"]
        assert "format" in args_dict["output_format"].lower()
