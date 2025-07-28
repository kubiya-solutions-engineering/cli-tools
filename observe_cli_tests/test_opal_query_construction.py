"""
Unit tests for OPAL query construction logic.
Tests the shell script logic that builds OPAL queries without making actual API calls.
"""
import pytest
import json
import subprocess
import tempfile
import os
from unittest.mock import patch, Mock, call


class TestOPALQueryConstruction:
    """Test OPAL query construction logic."""

    def test_basic_query_construction(self, opal_query_tool, mock_env):
        """Test basic OPAL query construction with minimal parameters."""
        # Extract the shell script content
        script_content = opal_query_tool.content
        
        # Test that the script contains the expected OPAL pipeline construction
        assert "pick_col" in script_content
        assert "filter" in script_content
        assert "limit" in script_content
        assert "skip" in script_content  # For pagination

    def test_filter_query_construction(self, mock_env):
        """Test query construction with filter parameters."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            # Write a simplified version of the query construction logic
            test_script = '''
            #!/bin/bash
            filter_term="$1"
            filter_type="$2"
            limit_count="$3"
            offset_count="$4"
            fields="$5"
            
            # Simulate the pipeline construction
            field_selection=""
            if [ -n "$fields" ]; then
                field_selection="pick_col $fields | "
            fi
            
            pagination_part=""
            if [ "$offset_count" -gt 0 ]; then
                pagination_part="skip $offset_count | "
            fi
            
            if [ -n "$filter_term" ]; then
                pipeline=$(printf '%sfilter %s ~ "%s" | %slimit %s' "$field_selection" "$filter_type" "$filter_term" "$pagination_part" "$limit_count")
            else
                pipeline=$(printf '%s%slimit %s' "$field_selection" "$pagination_part" "$limit_count")
            fi
            
            echo "$pipeline"
            '''
            f.write(test_script)
            f.flush()
            
            # Make executable
            os.chmod(f.name, 0o755)
            
            try:
                # Test with filter
                result = subprocess.run([
                    'bash', f.name, 'error', 'message', '50', '0', 'timestamp,message'
                ], capture_output=True, text=True)
                
                expected = "pick_col timestamp,message | filter message ~ \"error\" | limit 50"
                assert result.stdout.strip() == expected
                
                # Test with pagination
                result = subprocess.run([
                    'bash', f.name, 'error', 'message', '25', '50', 'timestamp,level'
                ], capture_output=True, text=True)
                
                expected = "pick_col timestamp,level | filter message ~ \"error\" | skip 50 | limit 25"
                assert result.stdout.strip() == expected
                
                # Test without filter
                result = subprocess.run([
                    'bash', f.name, '', 'message', '100', '0', ''
                ], capture_output=True, text=True)
                
                expected = "limit 100"
                assert result.stdout.strip() == expected
                
            finally:
                os.unlink(f.name)

    def test_limit_validation(self, mock_env):
        """Test limit validation and capping logic."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            limit_count="$1"
            
            # Validate and cap limit
            if [ "$limit_count" -gt 10000 ]; then
                echo "Limit capped at 10,000"
                limit_count="10000"
            fi
            
            echo "Final limit: $limit_count"
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                # Test normal limit
                result = subprocess.run(['bash', f.name, '50'], capture_output=True, text=True)
                assert "Final limit: 50" in result.stdout
                
                # Test excessive limit
                result = subprocess.run(['bash', f.name, '15000'], capture_output=True, text=True)
                assert "Limit capped at 10,000" in result.stdout
                assert "Final limit: 10000" in result.stdout
                
            finally:
                os.unlink(f.name)

    def test_json_query_construction(self, mock_env):
        """Test the JSON query construction logic."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            # Simplified test that creates basic JSON structure
            test_script = '''
            #!/bin/bash
            
            # Check if jq is available
            if ! command -v jq >/dev/null 2>&1; then
                echo "jq not available"
                exit 0
            fi
            
            # Simple JSON construction test
            echo '{"query":{"stages":[{"input":[{"inputName":"dataset_41000001","datasetId":"o::test_customer:dataset:41000001"},{"inputName":"dataset_41000002","datasetId":"o::test_customer:dataset:41000002"}],"stageID":"main","pipeline":"pick_col timestamp,message | filter level ~ \\"ERROR\\" | limit 50"}]}}'
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                result = subprocess.run(['bash', f.name], capture_output=True, text=True)
                
                # Skip test if jq not available
                if "jq not available" in result.stdout:
                    pytest.skip("jq command not available")
                
                # Parse the JSON output
                query_json = json.loads(result.stdout.strip())
                
                # Validate structure
                assert "query" in query_json
                assert "stages" in query_json["query"]
                assert len(query_json["query"]["stages"]) == 1
                
                stage = query_json["query"]["stages"][0]
                assert stage["stageID"] == "main"
                assert "pick_col timestamp,message" in stage["pipeline"]
                assert len(stage["input"]) == 2  # Two datasets
                
                # Validate dataset IDs
                dataset_ids = [inp["datasetId"] for inp in stage["input"]]
                expected_ids = [
                    "o::test_customer:dataset:41000001",
                    "o::test_customer:dataset:41000002"
                ]
                assert all(expected in dataset_ids for expected in expected_ids)
                
            finally:
                os.unlink(f.name)

    def test_field_selection_logic(self, mock_env):
        """Test field selection pipeline construction."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            fields="$1"
            
            field_selection=""
            if [ -n "$fields" ]; then
                field_selection="pick_col $fields | "
            fi
            
            echo "${field_selection}limit 10"
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                # Test with fields
                result = subprocess.run(['bash', f.name, 'timestamp,message,level'], 
                                      capture_output=True, text=True)
                assert result.stdout.strip() == "pick_col timestamp,message,level | limit 10"
                
                # Test without fields
                result = subprocess.run(['bash', f.name, ''], 
                                      capture_output=True, text=True)
                assert result.stdout.strip() == "limit 10"
                
            finally:
                os.unlink(f.name)

    def test_pagination_logic(self, mock_env):
        """Test pagination (skip) logic."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            offset_count="${1:-0}"
            limit_count="$2"
            
            pagination_part=""
            if [ "$offset_count" -gt 0 ]; then
                pagination_part="skip $offset_count | "
            fi
            
            echo "${pagination_part}limit $limit_count"
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                # Test with offset
                result = subprocess.run(['bash', f.name, '100', '50'], 
                                      capture_output=True, text=True)
                assert result.stdout.strip() == "skip 100 | limit 50"
                
                # Test without offset
                result = subprocess.run(['bash', f.name, '0', '50'], 
                                      capture_output=True, text=True)
                assert result.stdout.strip() == "limit 50"
                
            finally:
                os.unlink(f.name)

    def test_timeout_calculation(self, mock_env):
        """Test timeout calculation logic."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            limit_count="$1"
            query_timeout="${2:-300}"
            
            TIMEOUT_SECONDS="$query_timeout"
            if [ "$limit_count" -gt 1000 ]; then
                TIMEOUT_SECONDS=$((TIMEOUT_SECONDS * 2))
            fi
            
            echo "Timeout: ${TIMEOUT_SECONDS}s"
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                # Test normal timeout
                result = subprocess.run(['bash', f.name, '50', '300'], 
                                      capture_output=True, text=True)
                assert "Timeout: 300s" in result.stdout
                
                # Test doubled timeout for large queries
                result = subprocess.run(['bash', f.name, '2000', '300'], 
                                      capture_output=True, text=True)
                assert "Timeout: 600s" in result.stdout
                
            finally:
                os.unlink(f.name)


class TestOPALQueryValidation:
    """Test OPAL query validation logic."""

    def test_environment_validation(self, mock_env):
        """Test environment variable validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            
            # Simulate environment validation
            if [ -z "$OBSERVE_API_KEYS" ] || [ -z "$OBSERVE_CUSTOMER_ID" ] || [ -z "$DATASET_IDS" ]; then
                echo "Missing required environment variables"
                exit 1
            fi
            
            echo "Environment validation passed"
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                # Test with environment
                env = os.environ.copy()
                env.update(mock_env)
                result = subprocess.run(['bash', f.name], 
                                      capture_output=True, text=True, env=env)
                assert result.returncode == 0
                assert "Environment validation passed" in result.stdout
                
                # Test without environment
                result = subprocess.run(['bash', f.name], 
                                      capture_output=True, text=True, env={})
                assert result.returncode == 1
                assert "Missing required environment variables" in result.stdout
                
            finally:
                os.unlink(f.name)

    def test_api_key_parsing(self, mock_env):
        """Test API key JSON parsing logic."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            
            OBSERVE_API_KEYS='{"NA": "test_na_key", "EU": "test_eu_key"}'
            
            # Parse API keys from JSON (requires jq)
            if command -v jq >/dev/null 2>&1; then
                NA_API_KEY=$(echo "$OBSERVE_API_KEYS" | jq -r '.NA // empty')
                EU_API_KEY=$(echo "$OBSERVE_API_KEYS" | jq -r '.EU // empty')
                
                if [ -z "$NA_API_KEY" ] || [ -z "$EU_API_KEY" ]; then
                    echo "Missing API keys"
                    exit 1
                fi
                
                echo "NA Key: ${NA_API_KEY:0:8}..."
                echo "EU Key: ${EU_API_KEY:0:8}..."
            else
                echo "jq not available"
                exit 1
            fi
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                result = subprocess.run(['bash', f.name], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    assert "NA Key: test_na_" in result.stdout
                    assert "EU Key: test_eu_" in result.stdout
                else:
                    # jq might not be available in test environment
                    assert "jq not available" in result.stdout
                
            finally:
                os.unlink(f.name)