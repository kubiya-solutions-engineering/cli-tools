# Observe CLI Tools Test Suite

Comprehensive test suite for the Observe CLI Tools, covering unit tests, integration tests, performance tests, and error handling scenarios.

## Test Structure

```
tests/
├── __init__.py                     # Test package initialization
├── conftest.py                     # Pytest configuration and fixtures
├── fixtures.py                     # Mock data and test fixtures
├── test_runner.py                  # Test runner utilities
├── test_opal_query_construction.py # Unit tests for OPAL query logic
├── test_integration.py             # Integration tests for API interactions
├── test_pagination_and_errors.py   # Pagination and error handling tests
├── test_performance.py             # Performance and timeout tests
└── README.md                       # This file
```

## Quick Start

### Install Test Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `pytest>=7.0.0` - Test framework
- `pytest-mock>=3.10.0` - Mocking utilities
- `pytest-cov>=4.0.0` - Coverage reporting
- `responses>=0.23.0` - HTTP request mocking

### Run All Tests

```bash
# Run complete test suite with coverage
pytest

# Or use the test runner
python tests/test_runner.py all
```

### Run Specific Test Categories

```bash
# Unit tests only
python tests/test_runner.py unit

# Integration tests only  
python tests/test_runner.py integration

# Performance tests only
python tests/test_runner.py performance

# Validate test environment
python tests/test_runner.py validate
```

## Test Categories

### 🔧 Unit Tests (`test_opal_query_construction.py`)

Tests core OPAL query construction logic without external dependencies:

- **Query Pipeline Construction**: Tests building of OPAL pipelines with filters, field selection, and pagination
- **JSON Query Generation**: Tests generation of complete query JSON for API calls
- **Parameter Validation**: Tests validation of limits, offsets, and field selections
- **Environment Parsing**: Tests parsing of API keys and dataset IDs

**Key Test Cases:**
```python
def test_basic_query_construction()      # Basic pipeline building
def test_filter_query_construction()     # Filter parameter handling
def test_limit_validation()              # Limit capping and validation
def test_json_query_construction()       # Complete JSON generation
def test_field_selection_logic()         # Field selection pipeline
def test_pagination_logic()              # Skip/offset handling
```

### 🌐 Integration Tests (`test_integration.py`)

Tests complete API interaction flows:

- **API Call Success/Failure**: Tests successful API calls and various failure modes
- **Region Failover**: Tests US to EU region failover logic
- **Response Processing**: Tests handling of different response types and sizes
- **Progress Feedback**: Tests "Observing..." progress indicators
- **Tool Registration**: Tests Kubiya SDK tool registration

**Key Test Cases:**
```python
def test_successful_api_call_na_region()    # Successful API interaction
def test_region_failover_logic()            # Multi-region support
def test_large_response_streaming()         # Large response handling
def test_error_response_handling()          # API error scenarios
def test_progress_indicators()              # Progress feedback
```

### 📄 Pagination & Error Tests (`test_pagination_and_errors.py`)

Tests pagination logic and comprehensive error handling:

- **Pagination Logic**: Tests offset/skip functionality and pagination guidance
- **Error Scenarios**: Tests all possible error conditions and recovery
- **Environment Validation**: Tests missing/invalid environment variables
- **Graceful Degradation**: Tests fallback behaviors when components fail

**Key Test Cases:**
```python
def test_pagination_guidance_when_results_truncated()  # Pagination advice
def test_skip_clause_in_opal_query()                  # OPAL skip integration
def test_missing_environment_variables()              # Environment validation
def test_curl_error_handling()                        # HTTP error scenarios
def test_empty_or_invalid_response_handling()         # Response error handling
```

### ⚡ Performance Tests (`test_performance.py`)

Tests performance characteristics and resource optimization:

- **Timeout Handling**: Tests timeout calculation and handling for different query sizes
- **Resource Optimization**: Tests limit capping and field selection recommendations
- **Streaming Performance**: Tests streaming output for large responses
- **Memory Management**: Tests efficient processing of large JSON responses

**Key Test Cases:**
```python
def test_timeout_calculation_logic()           # Timeout scaling logic
def test_performance_guidance_based_on_response_size()  # Performance advice
def test_limit_capping_for_resource_protection() # Resource limits
def test_progressive_output_performance()       # Progress indicator timing
```

## Test Fixtures and Mock Data

### Mock Data (`fixtures.py`)

- **`MockData.sample_log_data()`**: Realistic log entries with proper field structure
- **`MockData.large_dataset(size)`**: Generate large datasets for pagination testing  
- **`MockData.error_scenarios()`**: Various API error responses
- **`MockEnvironments`**: Different environment configurations (valid, invalid, missing keys)
- **`MockQueries`**: Sample OPAL queries with expected results

### Test Fixtures (`conftest.py`)

- **`mock_env`**: Mock environment variables for testing
- **`sample_opal_response`**: Sample API response data
- **`cli_tools`**: CLITools instance for testing
- **`mock_curl_success/failure`**: Mock curl responses
- **`temp_workspace`**: Temporary workspace for file operations

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_opal_query_construction.py

# Run specific test method
pytest tests/test_integration.py::TestObserveAPIIntegration::test_successful_api_call_na_region
```

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=observe_cli_tools --cov-report=html

# View coverage in browser
open htmlcov/index.html
```

### Test Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests  
pytest -m integration

# Run only performance tests
pytest -m performance

# Skip slow tests
pytest -m "not slow"
```

## Test Environment Requirements

### System Dependencies

- **bash**: Required for shell script testing
- **jq**: Required for JSON processing tests (tests skip if not available)
- **curl**: Required for HTTP client testing
- **timeout**: Required for timeout testing (tests adapt if not available)

### Environment Variables (for integration tests)

```bash
export OBSERVE_API_KEYS='{"NA": "test_key_na", "EU": "test_key_eu"}'
export OBSERVE_CUSTOMER_ID="test_customer_123"  
export OBSERVE_DATASET_IDS="41000001,41000002"
```

## Test Coverage Targets

- **Overall Coverage**: ≥85%
- **Core Logic Coverage**: ≥95%
- **Error Handling Coverage**: ≥90%
- **Integration Coverage**: ≥80%

### Coverage Areas

✅ **Well Covered:**
- OPAL query construction logic
- Parameter validation and sanitization
- Error handling and recovery scenarios
- API response processing
- Pagination logic

⚠️ **Partial Coverage:**
- Shell script execution paths (platform-dependent)
- External command availability (jq, curl, timeout)
- Network failure scenarios (difficult to reproduce)

## Debugging Tests

### Debug Individual Tests

```bash
# Run with detailed output
pytest -vv tests/test_opal_query_construction.py::TestOPALQueryConstruction::test_basic_query_construction

# Run with PDB debugger
pytest --pdb tests/test_integration.py

# Show local variables in failures
pytest --tb=long tests/
```

### Test Data Inspection

```python
# In test files, inspect fixtures
def test_debug_fixtures(sample_opal_response, mock_env):
    import pprint
    pprint.pprint(sample_opal_response)
    pprint.pprint(mock_env)
    assert False  # Force failure to see output
```

## Writing New Tests

### Test Naming Convention

```python
def test_<functionality>_<scenario>():
    """Test <functionality> when <scenario>."""
    pass
```

### Mock Shell Scripts

```python
def test_shell_logic():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
        f.write('''#!/bin/bash
        echo "test output"
        ''')
        f.flush()
        os.chmod(f.name, 0o755)
        
        try:
            result = subprocess.run(['bash', f.name], capture_output=True, text=True)
            assert "test output" in result.stdout
        finally:
            os.unlink(f.name)
```

### Add Test Fixtures

```python
@pytest.fixture
def custom_fixture():
    """Custom fixture for specific test needs."""
    return {"key": "value"}
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python tests/test_runner.py validate
          python tests/test_runner.py report
```

## Troubleshooting

### Common Issues

**Tests fail with "jq not available"**
- Install jq: `brew install jq` (macOS) or `apt-get install jq` (Ubuntu)
- Tests will skip jq-dependent functionality if not available

**Coverage below threshold**
- Check uncovered lines: `pytest --cov-report=html`
- Add tests for missing coverage areas

**Integration tests fail**
- Verify mock environment variables are set correctly
- Check that responses library is installed

**Shell script tests fail**
- Ensure bash is available in PATH
- Check file permissions on temporary test files

### Getting Help

1. Check test output for specific error messages
2. Run `python tests/test_runner.py validate` to check environment
3. Use `pytest -vv` for detailed test output
4. Review test fixtures in `conftest.py` and `fixtures.py`