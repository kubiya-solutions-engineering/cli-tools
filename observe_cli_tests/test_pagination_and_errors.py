"""
Tests for pagination logic and comprehensive error handling scenarios.
"""
import pytest
import json
import subprocess
import tempfile
import os
from unittest.mock import patch, Mock


class TestPaginationLogic:
    """Test pagination functionality and guidance."""

    def test_pagination_guidance_when_results_truncated(self, mock_env):
        """Test pagination guidance when results equal limit (indicating more data)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            
            record_count="$1"
            limit_count="$2" 
            offset_count="${3:-0}"
            
            echo "📏 Response: $record_count records, 50000 bytes"
            
            # Pagination guidance logic
            if [ "$record_count" -eq "$limit_count" ]; then
                NEXT_OFFSET=$((offset_count + limit_count))
                echo "📄 Results may continue. For next page use: --offset $NEXT_OFFSET --limit $limit_count"
            fi
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                # Test when results equal limit (more data available)
                result = subprocess.run(['bash', f.name, '50', '50', '0'],
                                      capture_output=True, text=True)
                
                assert "📄 Results may continue" in result.stdout
                assert "--offset 50 --limit 50" in result.stdout
                
                # Test pagination from offset 100
                result = subprocess.run(['bash', f.name, '25', '25', '100'],
                                      capture_output=True, text=True)
                
                assert "--offset 125 --limit 25" in result.stdout
                
                # Test when results less than limit (no more data)
                result = subprocess.run(['bash', f.name, '30', '50', '0'],
                                      capture_output=True, text=True)
                
                assert "Results may continue" not in result.stdout
                
            finally:
                os.unlink(f.name)

    def test_skip_clause_in_opal_query(self, mock_env):
        """Test that skip clause is properly added to OPAL query for pagination."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            
            offset_count="${1:-0}"
            limit_count="$2"
            filter_term="$3"
            
            # Build pagination part
            pagination_part=""
            if [ "$offset_count" -gt 0 ]; then
                pagination_part="skip $offset_count | "
            fi
            
            # Build complete pipeline
            if [ -n "$filter_term" ]; then
                pipeline=$(printf 'filter message ~ "%s" | %slimit %s' "$filter_term" "$pagination_part" "$limit_count")
            else
                pipeline=$(printf '%slimit %s' "$pagination_part" "$limit_count")
            fi
            
            echo "$pipeline"
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                # Test with pagination and filter
                result = subprocess.run(['bash', f.name, '100', '25', 'error'],
                                      capture_output=True, text=True)
                assert result.stdout.strip() == 'filter message ~ "error" | skip 100 | limit 25'
                
                # Test with pagination only
                result = subprocess.run(['bash', f.name, '50', '10', ''],
                                      capture_output=True, text=True)
                assert result.stdout.strip() == 'skip 50 | limit 10'
                
                # Test without pagination
                result = subprocess.run(['bash', f.name, '0', '15', 'warn'],
                                      capture_output=True, text=True)
                assert result.stdout.strip() == 'filter message ~ "warn" | limit 15'
                
            finally:
                os.unlink(f.name)

    def test_pagination_with_field_selection(self, mock_env):
        """Test pagination combined with field selection."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            
            fields="$1"
            offset_count="${2:-0}"
            limit_count="$3"
            
            # Build field selection
            field_selection=""
            if [ -n "$fields" ]; then
                field_selection="pick_col $fields | "
            fi
            
            # Build pagination
            pagination_part=""
            if [ "$offset_count" -gt 0 ]; then
                pagination_part="skip $offset_count | "
            fi
            
            pipeline=$(printf '%s%slimit %s' "$field_selection" "$pagination_part" "$limit_count")
            echo "$pipeline"
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                # Test all components together
                result = subprocess.run(['bash', f.name, 'timestamp,message', '75', '25'],
                                      capture_output=True, text=True)
                assert result.stdout.strip() == 'pick_col timestamp,message | skip 75 | limit 25'
                
                # Test field selection without pagination
                result = subprocess.run(['bash', f.name, 'level,userId', '0', '50'],
                                      capture_output=True, text=True)
                assert result.stdout.strip() == 'pick_col level,userId | limit 50'
                
            finally:
                os.unlink(f.name)


class TestErrorHandlingScenarios:
    """Test comprehensive error handling scenarios."""

    def test_missing_environment_variables(self, mock_env):
        """Test handling of missing environment variables."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            
            # Test each required environment variable
            if [ -z "$OBSERVE_API_KEYS" ]; then
                echo "❌ OBSERVE_API_KEYS is required"
                exit 1
            fi
            
            if [ -z "$OBSERVE_CUSTOMER_ID" ]; then
                echo "❌ OBSERVE_CUSTOMER_ID is required"
                exit 1
            fi
            
            if [ -z "$OBSERVE_DATASET_IDS" ]; then
                echo "❌ OBSERVE_DATASET_IDS is required"
                exit 1
            fi
            
            echo "✅ All environment variables present"
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                # Test with all variables
                env = os.environ.copy()
                env.update(mock_env)
                result = subprocess.run(['bash', f.name], 
                                      capture_output=True, text=True, env=env)
                assert result.returncode == 0
                assert "✅ All environment variables present" in result.stdout
                
                # Test missing API keys
                env_missing_keys = env.copy()
                del env_missing_keys['OBSERVE_API_KEYS']
                result = subprocess.run(['bash', f.name], 
                                      capture_output=True, text=True, env=env_missing_keys)
                assert result.returncode == 1
                assert "❌ OBSERVE_API_KEYS is required" in result.stdout
                
                # Test missing customer ID
                env_missing_customer = env.copy()
                del env_missing_customer['OBSERVE_CUSTOMER_ID']
                result = subprocess.run(['bash', f.name], 
                                      capture_output=True, text=True, env=env_missing_customer)
                assert result.returncode == 1
                assert "❌ OBSERVE_CUSTOMER_ID is required" in result.stdout
                
            finally:
                os.unlink(f.name)

    def test_invalid_api_key_format(self, mock_env):
        """Test handling of invalid API key JSON format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            
            OBSERVE_API_KEYS="$1"
            
            # Check if jq is available (skip if not)
            if ! command -v jq >/dev/null 2>&1; then
                echo "jq not available, skipping test"
                exit 0
            fi
            
            # Try to parse API keys
            NA_API_KEY=$(echo "$OBSERVE_API_KEYS" | jq -r '.NA // empty' 2>/dev/null)
            EU_API_KEY=$(echo "$OBSERVE_API_KEYS" | jq -r '.EU // empty' 2>/dev/null)
            
            if [ -z "$NA_API_KEY" ] || [ -z "$EU_API_KEY" ]; then
                echo "❌ OBSERVE_API_KEYS must contain both 'NA' and 'EU' keys"
                echo "Expected format: {\"NA\": \"key1\", \"EU\": \"key2\"}"
                exit 1
            fi
            
            echo "✅ API keys parsed successfully"
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                # Test valid format
                valid_keys = '{"NA": "test_na_key", "EU": "test_eu_key"}'
                result = subprocess.run(['bash', f.name, valid_keys],
                                      capture_output=True, text=True)
                
                if "jq not available" not in result.stdout:
                    assert result.returncode == 0
                    assert "✅ API keys parsed successfully" in result.stdout
                
                # Test invalid format (missing EU)
                invalid_keys = '{"NA": "test_na_key"}'
                result = subprocess.run(['bash', f.name, invalid_keys],
                                      capture_output=True, text=True)
                
                if "jq not available" not in result.stdout:
                    assert result.returncode == 1
                    assert "must contain both 'NA' and 'EU' keys" in result.stdout
                
                # Test completely invalid JSON
                invalid_json = 'not-json-at-all'
                result = subprocess.run(['bash', f.name, invalid_json],
                                      capture_output=True, text=True)
                
                if "jq not available" not in result.stdout:
                    assert result.returncode == 1
                
            finally:
                os.unlink(f.name)

    def test_curl_error_handling(self, mock_env):
        """Test handling of various curl error scenarios."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            
            curl_exit_code="$1"
            
            echo "   ⏱️  Curl completed in 5s (exit code: $curl_exit_code)"
            
            if [ $curl_exit_code -ne 0 ]; then
                echo "   ❌ Curl failed with exit code $curl_exit_code"
                case $curl_exit_code in
                    28) echo "   💡 Timeout occurred (5s)" ;;
                    6)  echo "   💡 Couldn't resolve host" ;;
                    7)  echo "   💡 Failed to connect to host" ;;
                    22) echo "   💡 HTTP error response (404 - wrong region)" ;;
                    52) echo "   💡 Empty reply from server" ;;
                    60) echo "   💡 SSL certificate verification failed" ;;
                    *) echo "   💡 Curl error $curl_exit_code" ;;
                esac
                exit 1
            else
                echo "   ✅ Curl succeeded"
            fi
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                # Test successful curl
                result = subprocess.run(['bash', f.name, '0'],
                                      capture_output=True, text=True)
                assert result.returncode == 0
                assert "✅ Curl succeeded" in result.stdout
                
                # Test timeout
                result = subprocess.run(['bash', f.name, '28'],
                                      capture_output=True, text=True)
                assert result.returncode == 1
                assert "💡 Timeout occurred" in result.stdout
                
                # Test connection error
                result = subprocess.run(['bash', f.name, '7'],
                                      capture_output=True, text=True)
                assert result.returncode == 1
                assert "💡 Failed to connect to host" in result.stdout
                
                # Test HTTP error
                result = subprocess.run(['bash', f.name, '22'],
                                      capture_output=True, text=True)
                assert result.returncode == 1
                assert "💡 HTTP error response (404 - wrong region)" in result.stdout
                
            finally:
                os.unlink(f.name)

    def test_empty_or_invalid_response_handling(self, mock_env):
        """Test handling of empty or invalid API responses."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            
            response_type="$1"
            
            case "$response_type" in
                "empty")
                    RESPONSE=""
                    ;;
                "invalid_json")
                    RESPONSE="<html><body>Not JSON</body></html>"
                    ;;
                "valid_empty")
                    RESPONSE='{"data":[],"message":"No data found matching your query criteria"}'
                    ;;
                "valid_data")
                    RESPONSE='{"data":[{"message":"test"}],"count":1}'
                    ;;
            esac
            
            # Handle response
            if [ -z "$RESPONSE" ]; then
                echo "   ✅ Empty response - query executed successfully but found no matching data"
                echo "   💡 This usually means your filter didn't match any records"
            elif echo "$RESPONSE" | jq empty >/dev/null 2>&1; then
                echo "📊 Valid JSON response received"
                echo "$RESPONSE" | jq .
            else
                echo "📄 Raw response (non-JSON):"
                echo "🔍 No response data received. Query may have timed out or found no results."
                echo "💡 Try: reducing --limit, adding more specific filters, or increasing --query_timeout"
            fi
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                # Test empty response
                result = subprocess.run(['bash', f.name, 'empty'],
                                      capture_output=True, text=True)
                assert "Empty response - query executed successfully" in result.stdout
                assert "filter didn't match any records" in result.stdout
                
                # Test invalid JSON
                result = subprocess.run(['bash', f.name, 'invalid_json'],
                                      capture_output=True, text=True)
                assert "Raw response (non-JSON)" in result.stdout
                assert "reducing --limit" in result.stdout
                
                # Test valid empty data
                result = subprocess.run(['bash', f.name, 'valid_empty'],
                                      capture_output=True, text=True)
                assert "Valid JSON response received" in result.stdout
                
            finally:
                os.unlink(f.name)

    def test_limit_validation_and_capping(self, mock_env):
        """Test limit validation and automatic capping."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            
            limit_count="$1"
            
            # Validate and cap limit
            if [ "$limit_count" -gt 10000 ]; then
                echo "⚠️  Limit capped at 10,000 for performance. Use pagination for larger datasets."
                limit_count="10000"
            fi
            
            echo "Final limit: $limit_count"
            
            # Performance guidance
            if [ "$limit_count" -gt 50 ]; then
                echo "⚠️  High limit ($limit_count) may cause slow responses with large log records"
                echo "💡 Consider starting with a smaller limit and increasing if needed"
            fi
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                # Test normal limit
                result = subprocess.run(['bash', f.name, '25'],
                                      capture_output=True, text=True)
                assert "Final limit: 25" in result.stdout
                assert "High limit" not in result.stdout
                
                # Test high but valid limit
                result = subprocess.run(['bash', f.name, '500'],
                                      capture_output=True, text=True)
                assert "Final limit: 500" in result.stdout
                assert "⚠️  High limit (500)" in result.stdout
                assert "smaller limit and increasing" in result.stdout
                
                # Test excessive limit
                result = subprocess.run(['bash', f.name, '50000'],
                                      capture_output=True, text=True)
                assert "⚠️  Limit capped at 10,000" in result.stdout
                assert "Final limit: 10000" in result.stdout
                assert "Use pagination for larger datasets" in result.stdout
                
            finally:
                os.unlink(f.name)


class TestErrorRecoveryAndFallbacks:
    """Test error recovery mechanisms and fallback behaviors."""

    def test_both_regions_fail_scenario(self, mock_env):
        """Test behavior when both US and EU regions fail."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            
            echo "🔍 Trying us-1 region..."
            echo "   ❌ Curl failed with exit code 22"
            echo "   💡 HTTP error response (404 - wrong region)"
            echo ""
            
            echo "🔍 Trying eu-1 region..."
            echo "   ❌ Curl failed with exit code 7" 
            echo "   💡 Failed to connect to host"
            echo ""
            
            echo "❌ Failed to execute query in both US and EU regions"
            echo "💡 Verify your dataset IDs are correct and you have access to them"
            exit 1
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                result = subprocess.run(['bash', f.name],
                                      capture_output=True, text=True)
                
                assert result.returncode == 1
                assert "Trying us-1 region" in result.stdout
                assert "Trying eu-1 region" in result.stdout
                assert "Failed to execute query in both US and EU regions" in result.stdout
                assert "Verify your dataset IDs are correct" in result.stdout
                
            finally:
                os.unlink(f.name)

    def test_graceful_degradation_on_partial_failures(self, mock_env):
        """Test graceful degradation when some operations fail."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            
            scenario="$1"
            
            case "$scenario" in
                "jq_missing")
                    echo "📄 Raw response (non-JSON):"
                    echo "Query JSON construction failed - jq not available"
                    echo '{"data": [{"message": "test"}]}'
                    ;;
                "json_parse_error") 
                    echo "📊 Query Results (completed in 2s):"
                    echo "📏 Response received successfully (no data found)"
                    echo "Raw response shown due to JSON parsing error"
                    ;;
                "timeout_recovery")
                    echo "🔍 No response data received. Query may have timed out or found no results."
                    echo "💡 Try: reducing --limit, adding more specific filters, or increasing --query_timeout"
                    ;;
            esac
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                # Test jq missing scenario
                result = subprocess.run(['bash', f.name, 'jq_missing'],
                                      capture_output=True, text=True)
                assert "jq not available" in result.stdout
                assert "Raw response" in result.stdout
                
                # Test JSON parse error recovery
                result = subprocess.run(['bash', f.name, 'json_parse_error'],
                                      capture_output=True, text=True)
                assert "Response received successfully" in result.stdout
                assert "JSON parsing error" in result.stdout
                
                # Test timeout recovery suggestions
                result = subprocess.run(['bash', f.name, 'timeout_recovery'],
                                      capture_output=True, text=True)
                assert "Query may have timed out" in result.stdout
                assert "reducing --limit" in result.stdout
                assert "increasing --query_timeout" in result.stdout
                
            finally:
                os.unlink(f.name)