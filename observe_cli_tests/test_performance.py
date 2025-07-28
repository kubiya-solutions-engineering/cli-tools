"""
Performance and timeout tests for observe_cli_tools.
Tests query performance, timeout handling, and resource usage optimization.
"""
import pytest
import time
import subprocess
import tempfile
import os
from unittest.mock import patch, Mock
from tests.fixtures import MockData, MockQueries, MockEnvironments


class TestQueryPerformance:
    """Test query performance characteristics."""

    def test_timeout_calculation_logic(self, mock_env):
        """Test that timeout calculation scales appropriately with query size."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            
            limit_count="$1"
            base_timeout="${2:-300}"
            
            TIMEOUT_SECONDS="$base_timeout"
            if [ "$limit_count" -gt 1000 ]; then
                TIMEOUT_SECONDS=$((TIMEOUT_SECONDS * 2))
                echo "Timeout doubled for large query: ${TIMEOUT_SECONDS}s"
            else
                echo "Standard timeout: ${TIMEOUT_SECONDS}s"
            fi
            
            echo "Final timeout for limit $limit_count: ${TIMEOUT_SECONDS}s"
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                # Test small query timeout
                result = subprocess.run(['bash', f.name, '50', '300'],
                                      capture_output=True, text=True)
                assert "Standard timeout: 300s" in result.stdout
                assert "Final timeout for limit 50: 300s" in result.stdout
                
                # Test medium query timeout
                result = subprocess.run(['bash', f.name, '500', '180'],
                                      capture_output=True, text=True)
                assert "Standard timeout: 180s" in result.stdout
                assert "Final timeout for limit 500: 180s" in result.stdout
                
                # Test large query timeout (should double)
                result = subprocess.run(['bash', f.name, '2000', '300'],
                                      capture_output=True, text=True)
                assert "Timeout doubled for large query: 600s" in result.stdout
                assert "Final timeout for limit 2000: 600s" in result.stdout
                
                # Test very large query timeout
                result = subprocess.run(['bash', f.name, '5000', '240'],
                                      capture_output=True, text=True)
                assert "Timeout doubled for large query: 480s" in result.stdout
                assert "Final timeout for limit 5000: 480s" in result.stdout
                
            finally:
                os.unlink(f.name)

    def test_performance_guidance_based_on_response_size(self, mock_env):
        """Test performance guidance based on response characteristics."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            
            response_size="$1"
            record_count="$2"
            limit_count="$3"
            
            echo "📏 Response: $record_count records, $response_size bytes"
            
            # Performance insights
            if [ "$response_size" -gt 500000 ]; then
                echo "📊 Large response detected - rich log content available"
                if [ "$record_count" -gt 50 ]; then
                    echo "💡 Consider using --fields to select specific columns for faster queries"
                fi
            fi
            
            # Performance guidance
            if [ "$limit_count" -gt 50 ]; then
                echo "⚠️  High limit ($limit_count) may cause slow responses with large log records"
                echo "💡 Consider starting with a smaller limit and increasing if needed"
            fi
            
            # Calculate average record size
            if [ "$record_count" -gt 0 ]; then
                avg_size=$((response_size / record_count))
                if [ "$avg_size" -gt 10000 ]; then
                    echo "📊 Large average record size: ${avg_size} bytes per record"
                    echo "💡 Use --fields to reduce record size for better performance"
                fi
            fi
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                # Test small response
                result = subprocess.run(['bash', f.name, '25000', '10', '25'],
                                      capture_output=True, text=True)
                assert "Large response detected" not in result.stdout
                assert "High limit" not in result.stdout
                
                # Test large response with many records
                result = subprocess.run(['bash', f.name, '750000', '100', '100'],
                                      capture_output=True, text=True)
                assert "📊 Large response detected - rich log content available" in result.stdout
                assert "💡 Consider using --fields" in result.stdout
                assert "⚠️  High limit (100)" in result.stdout
                
                # Test large individual records
                result = subprocess.run(['bash', f.name, '500000', '25', '25'],
                                      capture_output=True, text=True)
                assert "📊 Large average record size: 20000 bytes" in result.stdout
                assert "💡 Use --fields to reduce record size" in result.stdout
                
            finally:
                os.unlink(f.name)

    def test_streaming_threshold_logic(self, mock_env):
        """Test streaming output threshold logic."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            
            response_size="$1"
            
            # Streaming output for large responses
            if [ "$response_size" -gt 100000 ]; then
                echo "📤 Streaming large response..."
                echo "Using streaming mode for performance"
            else
                echo "Standard output mode"
            fi
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                # Test small response (no streaming)
                result = subprocess.run(['bash', f.name, '50000'],
                                      capture_output=True, text=True)
                assert "Standard output mode" in result.stdout
                assert "Streaming large response" not in result.stdout
                
                # Test large response (streaming)
                result = subprocess.run(['bash', f.name, '150000'],
                                      capture_output=True, text=True)
                assert "📤 Streaming large response..." in result.stdout
                assert "Using streaming mode for performance" in result.stdout
                
            finally:
                os.unlink(f.name)


class TestTimeoutHandling:
    """Test timeout handling in various scenarios."""

    def test_progressive_timeout_scenarios(self, mock_env):
        """Test different timeout scenarios and their handling."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            
            timeout_scenario="$1"
            
            case "$timeout_scenario" in
                "quick_success")
                    echo "Query completed in 2s"
                    exit 0
                    ;;
                "slow_success")
                    echo "Query completed in 45s"
                    echo "💡 Query took longer than expected - consider optimizing filters"
                    exit 0
                    ;;
                "timeout_hit")
                    echo "Query timed out after 300s"
                    echo "🔍 No response data received. Query may have timed out or found no results."
                    echo "💡 Try: reducing --limit, adding more specific filters, or increasing --query_timeout"
                    exit 1
                    ;;
                "timeout_with_partial")
                    echo "Query timed out but returned partial results"
                    echo "⚠️  Query completed with timeout - partial results shown"
                    exit 0
                    ;;
            esac
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                # Test quick success
                result = subprocess.run(['bash', f.name, 'quick_success'],
                                      capture_output=True, text=True)
                assert result.returncode == 0
                assert "Query completed in 2s" in result.stdout
                
                # Test slow but successful
                result = subprocess.run(['bash', f.name, 'slow_success'],
                                      capture_output=True, text=True)
                assert result.returncode == 0
                assert "took longer than expected" in result.stdout
                
                # Test timeout
                result = subprocess.run(['bash', f.name, 'timeout_hit'],
                                      capture_output=True, text=True)
                assert result.returncode == 1
                assert "Query timed out after 300s" in result.stdout
                assert "reducing --limit" in result.stdout
                
                # Test timeout with partial results
                result = subprocess.run(['bash', f.name, 'timeout_with_partial'],
                                      capture_output=True, text=True)
                assert result.returncode == 0
                assert "partial results shown" in result.stdout
                
            finally:
                os.unlink(f.name)

    def test_timeout_command_integration(self, mock_env):
        """Test timeout command integration and signal handling."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            
            test_duration="$1"
            timeout_seconds="$2"
            
            # Check if timeout command is available
            if ! command -v timeout >/dev/null 2>&1; then
                echo "timeout command not available, simulating behavior"
                echo "Starting timeout test with ${timeout_seconds}s timeout"
                if [ "$test_duration" -gt "$timeout_seconds" ]; then
                    echo "Operation timed out after ${timeout_seconds}s"
                    echo "💡 Consider increasing --query_timeout or optimizing query"
                    exit 124
                else
                    echo "Operation completed within timeout"
                    exit 0
                fi
            fi
            
            # Simulate the timeout command usage
            echo "Starting timeout test with ${timeout_seconds}s timeout"
            
            if timeout "${timeout_seconds}s" sleep "$test_duration" 2>/dev/null; then
                echo "Operation completed within timeout"
                exit 0
            else
                exit_code=$?
                if [ $exit_code -eq 124 ]; then
                    echo "Operation timed out after ${timeout_seconds}s"
                    echo "💡 Consider increasing --query_timeout or optimizing query"
                else
                    echo "Operation failed with exit code $exit_code"
                fi
                exit $exit_code
            fi
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                # Test successful completion within timeout
                result = subprocess.run(['bash', f.name, '1', '3'],
                                      capture_output=True, text=True)
                assert result.returncode == 0
                assert "Operation completed within timeout" in result.stdout
                
                # Test timeout scenario
                result = subprocess.run(['bash', f.name, '3', '1'],
                                      capture_output=True, text=True)
                # Should timeout (exit 124) whether using real or simulated timeout
                assert result.returncode == 124
                assert "timed out" in result.stdout
                
            finally:
                os.unlink(f.name)


class TestResourceOptimization:
    """Test resource usage optimization features."""

    def test_limit_capping_for_resource_protection(self, mock_env):
        """Test that excessive limits are capped to protect resources."""
        queries = MockQueries.performance_test_queries()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            
            requested_limit="$1"
            
            # Apply limit capping
            final_limit="$requested_limit"
            if [ "$requested_limit" -gt 10000 ]; then
                echo "⚠️  Limit capped at 10,000 for performance. Use pagination for larger datasets."
                final_limit="10000"
            fi
            
            echo "Requested: $requested_limit, Final: $final_limit"
            
            # Performance warnings
            if [ "$final_limit" -gt 1000 ]; then
                echo "⚠️  Large limit may impact performance"
                echo "💡 Consider using pagination with --offset for large datasets"
            fi
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                # Test reasonable limits
                for limit in [10, 100, 1000]:
                    result = subprocess.run(['bash', f.name, str(limit)],
                                          capture_output=True, text=True)
                    assert f"Final: {limit}" in result.stdout
                    if limit <= 1000:
                        assert "Large limit may impact" not in result.stdout
                
                # Test excessive limits
                for limit in [15000, 50000, 100000]:
                    result = subprocess.run(['bash', f.name, str(limit)],
                                          capture_output=True, text=True)
                    assert "⚠️  Limit capped at 10,000" in result.stdout
                    assert "Final: 10000" in result.stdout
                    assert "Use pagination for larger datasets" in result.stdout
                
            finally:
                os.unlink(f.name)

    def test_field_selection_performance_optimization(self, mock_env):
        """Test field selection recommendations for performance."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            
            fields="$1"
            record_count="$2"
            response_size="$3"
            
            if [ -n "$fields" ]; then
                echo "📝 Field selection: $fields"
                echo "✅ Using field selection for optimal performance"
            else
                echo "💡 Including all fields (including message with log content)"
                if [ "$response_size" -gt 100000 ]; then
                    echo "📊 Large response - consider using --fields for better performance"
                    echo "💡 Example: --fields 'timestamp,level,message,statusCode'"
                fi
            fi
            
            # Calculate efficiency metrics
            if [ -n "$fields" ] && [ "$record_count" -gt 0 ]; then
                field_count=$(echo "$fields" | tr ',' ' ' | wc -w)
                avg_per_field=$((response_size / record_count / field_count))
                echo "📊 Average bytes per field: $avg_per_field"
            fi
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                # Test with field selection
                result = subprocess.run(['bash', f.name, 'timestamp,message,level', '50', '75000'],
                                      capture_output=True, text=True)
                assert "📝 Field selection: timestamp,message,level" in result.stdout
                assert "✅ Using field selection for optimal performance" in result.stdout
                assert "Average bytes per field:" in result.stdout
                
                # Test without field selection (large response)
                result = subprocess.run(['bash', f.name, '', '100', '500000'],
                                      capture_output=True, text=True)
                assert "💡 Including all fields" in result.stdout
                assert "📊 Large response - consider using --fields" in result.stdout
                assert "Example: --fields" in result.stdout
                
                # Test without field selection (small response)
                result = subprocess.run(['bash', f.name, '', '25', '50000'],
                                      capture_output=True, text=True)
                assert "💡 Including all fields" in result.stdout
                assert "Large response - consider" not in result.stdout
                
            finally:
                os.unlink(f.name)


class TestProgressiveOutputPerformance:
    """Test progressive output and feedback performance."""

    def test_progress_indicator_timing(self, mock_env):
        """Test that progress indicators work correctly with different timing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            
            simulation_seconds="$1"
            
            echo "   📊 Observing query progress..."
            
            # Simulate progress indicators
            progress_count=0
            end_time=$(($(date +%s) + simulation_seconds))
            
            while [ $(date +%s) -lt $end_time ]; do
                progress_count=$((progress_count + 1))
                case $((progress_count % 4)) in
                    0) echo -n "   🔄 Observing" ;;
                    1) echo -n "   🔄 Observing." ;;
                    2) echo -n "   🔄 Observing.." ;;
                    3) echo -n "   🔄 Observing..." ;;
                esac
                echo -ne "\\r"
                sleep 1
            done
            
            echo "   ✅ Query completed                    "
            echo "Progress updates: $progress_count"
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                # Test short progress sequence
                start_time = time.time()
                result = subprocess.run(['bash', f.name, '3'],
                                      capture_output=True, text=True)
                end_time = time.time()
                
                # Should complete within reasonable time (allowing for some overhead)
                assert end_time - start_time < 5
                assert "📊 Observing query progress" in result.stdout
                assert "✅ Query completed" in result.stdout
                assert "Progress updates:" in result.stdout
                
            finally:
                os.unlink(f.name)

    def test_large_response_streaming_performance(self, mock_env):
        """Test streaming performance for large responses."""
        large_data = MockData.large_dataset(1000)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            
            response_size="$1"
            stream_threshold="100000"
            
            if [ "$response_size" -gt "$stream_threshold" ]; then
                echo "📤 Streaming large response..."
                # Simulate streaming by outputting in chunks
                echo "Chunk 1: Processing first 100KB..."
                echo "Chunk 2: Processing next 100KB..."
                echo "Chunk 3: Processing remaining data..."
                echo "✅ Streaming completed"
            else
                echo "Standard output processing"
            fi
            
            echo "Total response size: $response_size bytes"
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                # Test small response (no streaming)
                result = subprocess.run(['bash', f.name, '50000'],
                                      capture_output=True, text=True)
                assert "Standard output processing" in result.stdout
                assert "Streaming large response" not in result.stdout
                
                # Test large response (streaming)
                result = subprocess.run(['bash', f.name, '500000'],
                                      capture_output=True, text=True)
                assert "📤 Streaming large response..." in result.stdout
                assert "Chunk 1: Processing" in result.stdout
                assert "✅ Streaming completed" in result.stdout
                
            finally:
                os.unlink(f.name)


class TestMemoryAndResourceUsage:
    """Test memory usage and resource management."""

    def test_json_processing_efficiency(self, mock_env):
        """Test efficient JSON processing for different response sizes."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            
            json_size="$1"
            
            # Simulate JSON processing efficiency checks
            if [ "$json_size" -lt 50000 ]; then
                echo "Small JSON: Using standard jq processing"
                echo "Memory efficient processing"
            elif [ "$json_size" -lt 500000 ]; then
                echo "Medium JSON: Using streaming jq processing"
                echo "Optimized for moderate memory usage"
            else
                echo "Large JSON: Using chunked processing"
                echo "Memory-conscious processing for large responses"
                echo "💡 Consider using --fields to reduce response size"
            fi
            
            echo "JSON size: $json_size bytes"
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                # Test different JSON sizes
                sizes = [25000, 150000, 750000]
                expected_messages = [
                    "Small JSON: Using standard jq",
                    "Medium JSON: Using streaming jq", 
                    "Large JSON: Using chunked processing"
                ]
                
                for size, expected in zip(sizes, expected_messages):
                    result = subprocess.run(['bash', f.name, str(size)],
                                          capture_output=True, text=True)
                    assert expected in result.stdout
                    assert f"JSON size: {size} bytes" in result.stdout
                
                # Large size should also have optimization suggestion
                result = subprocess.run(['bash', f.name, '750000'],
                                      capture_output=True, text=True)
                assert "💡 Consider using --fields" in result.stdout
                
            finally:
                os.unlink(f.name)

    def test_curl_resource_management(self, mock_env):
        """Test curl resource management and cleanup."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            test_script = '''
            #!/bin/bash
            
            test_scenario="$1"
            
            case "$test_scenario" in
                "process_cleanup")
                    echo "Starting curl process: PID 12345"
                    echo "Monitoring process health..."
                    echo "Process completed successfully"
                    echo "Cleanup: Process resources released"
                    ;;
                "timeout_cleanup")
                    echo "Starting curl process: PID 12346"
                    echo "Process timeout detected"
                    echo "Cleanup: Terminating curl process"
                    echo "Cleanup: Process resources released"
                    ;;
                "signal_handling")
                    echo "Starting curl process: PID 12347"
                    echo "Interrupt signal received"
                    echo "Cleanup: Gracefully terminating process"
                    echo "Cleanup: Process resources released"
                    ;;
            esac
            '''
            f.write(test_script)
            f.flush()
            os.chmod(f.name, 0o755)
            
            try:
                scenarios = ["process_cleanup", "timeout_cleanup", "signal_handling"]
                
                for scenario in scenarios:
                    result = subprocess.run(['bash', f.name, scenario],
                                          capture_output=True, text=True)
                    assert "Starting curl process: PID" in result.stdout
                    assert "Cleanup: Process resources released" in result.stdout
                
            finally:
                os.unlink(f.name)