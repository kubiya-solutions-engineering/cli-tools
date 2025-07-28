"""
Test fixtures and mock data for observe_cli_tools tests.
Contains realistic sample data and test scenarios.
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any


class MockData:
    """Container for mock data used in tests."""
    
    @staticmethod
    def sample_log_data() -> List[Dict[str, Any]]:
        """Generate sample log entries that resemble real Observe data."""
        base_time = datetime(2024, 1, 15, 10, 30, 0)
        
        return [
            {
                "timestamp": base_time.isoformat() + "Z",
                "level": "ERROR",
                "message": "Database connection failed: Connection timeout after 30s",
                "applicationName": "web-service",
                "statusCode": 500,
                "httpMethod": "GET",
                "requestURI": "/api/users/123",
                "userId": "user_12345",
                "endpoint": "/api/users",
                "sleuthTraceId": "trace_abc_123",
                "sleuthSpanId": "span_def_456", 
                "node": "web-01.prod.company.com",
                "company": "acme-corp",
                "tenantId": "tenant_789"
            },
            {
                "timestamp": (base_time + timedelta(minutes=1)).isoformat() + "Z",
                "level": "WARN",
                "message": "High memory usage detected: 85% of available memory in use",
                "applicationName": "worker-service",
                "statusCode": 200,
                "httpMethod": "POST",
                "requestURI": "/api/jobs/process",
                "userId": "user_67890",
                "endpoint": "/api/jobs",
                "sleuthTraceId": "trace_ghi_789",
                "sleuthSpanId": "span_jkl_012",
                "node": "worker-02.prod.company.com",
                "company": "acme-corp",
                "tenantId": "tenant_456"
            },
            {
                "timestamp": (base_time + timedelta(minutes=2)).isoformat() + "Z",
                "level": "INFO",
                "message": "User authentication successful",
                "applicationName": "auth-service",
                "statusCode": 200,
                "httpMethod": "POST",
                "requestURI": "/auth/login",
                "userId": "user_11111",
                "endpoint": "/auth/login",
                "sleuthTraceId": "trace_mno_345",
                "sleuthSpanId": "span_pqr_678",
                "node": "auth-01.prod.company.com",
                "company": "acme-corp",
                "tenantId": "tenant_789"
            },
            {
                "timestamp": (base_time + timedelta(minutes=3)).isoformat() + "Z",
                "level": "ERROR",
                "message": "Payment processing failed: Invalid credit card number",
                "applicationName": "payment-service",
                "statusCode": 400,
                "httpMethod": "POST",
                "requestURI": "/api/payments/charge",
                "userId": "user_22222",
                "endpoint": "/api/payments",
                "sleuthTraceId": "trace_stu_901",
                "sleuthSpanId": "span_vwx_234",
                "node": "payment-01.prod.company.com",
                "company": "beta-corp",
                "tenantId": "tenant_123"
            },
            {
                "timestamp": (base_time + timedelta(minutes=4)).isoformat() + "Z",
                "level": "DEBUG",
                "message": "Cache miss for key: user_profile_33333",
                "applicationName": "cache-service",
                "statusCode": 200,
                "httpMethod": "GET",
                "requestURI": "/cache/get/user_profile_33333",
                "userId": "user_33333",
                "endpoint": "/cache/get",
                "sleuthTraceId": "trace_yz_567",
                "sleuthSpanId": "span_ab_890",
                "node": "cache-01.prod.company.com",
                "company": "acme-corp",
                "tenantId": "tenant_789"
            }
        ]

    @staticmethod
    def large_dataset(size: int = 100) -> List[Dict[str, Any]]:
        """Generate a large dataset for pagination testing."""
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        data = []
        
        services = ["web-service", "api-service", "worker-service", "auth-service", "payment-service"]
        levels = ["INFO", "WARN", "ERROR", "DEBUG"]
        methods = ["GET", "POST", "PUT", "DELETE"]
        status_codes = [200, 201, 400, 401, 404, 500, 502, 503]
        
        for i in range(size):
            timestamp = base_time + timedelta(minutes=i)
            service = services[i % len(services)]
            level = levels[i % len(levels)]
            method = methods[i % len(methods)]
            status = status_codes[i % len(status_codes)]
            
            data.append({
                "timestamp": timestamp.isoformat() + "Z",
                "level": level,
                "message": f"Log entry {i+1}: Processing request for user_{i+1000}",
                "applicationName": service,
                "statusCode": status,
                "httpMethod": method,
                "requestURI": f"/api/resource/{i+1}",
                "userId": f"user_{i+1000}",
                "endpoint": f"/api/resource",
                "sleuthTraceId": f"trace_{i:04d}",
                "sleuthSpanId": f"span_{i:04d}",
                "node": f"{service.split('-')[0]}-{(i%3)+1:02d}.prod.company.com",
                "company": "test-corp",
                "tenantId": f"tenant_{(i%5)+1}"
            })
        
        return data

    @staticmethod
    def error_scenarios() -> Dict[str, Dict[str, Any]]:
        """Generate error response scenarios for testing."""
        return {
            "auth_error": {
                "error": "Authentication failed",
                "code": 401,
                "message": "Invalid API key or insufficient permissions",
                "details": {
                    "hint": "Check your OBSERVE_API_KEYS environment variable"
                }
            },
            "not_found": {
                "error": "Dataset not found", 
                "code": 404,
                "message": "The specified dataset ID does not exist or is not accessible",
                "details": {
                    "hint": "Verify dataset ID in OBSERVE_DATASET_IDS environment variable"
                }
            },
            "rate_limit": {
                "error": "Rate limit exceeded",
                "code": 429,
                "message": "Too many requests. Please wait before retrying.",
                "details": {
                    "retry_after": 60,
                    "hint": "Reduce query frequency or contact support for higher limits"
                }
            },
            "server_error": {
                "error": "Internal server error",
                "code": 500,
                "message": "An unexpected error occurred while processing your request",
                "details": {
                    "request_id": "req_abc123def456",
                    "hint": "Please retry. If error persists, contact support with request ID"
                }
            },
            "timeout": {
                "error": "Query timeout",
                "code": 408,
                "message": "Query execution exceeded maximum allowed time",
                "details": {
                    "timeout_seconds": 300,
                    "hint": "Try reducing --limit or adding more specific filters"
                }
            },
            "bad_request": {
                "error": "Invalid query",
                "code": 400,
                "message": "OPAL query syntax error",
                "details": {
                    "query_error": "Syntax error near 'filter'",
                    "hint": "Check OPAL query syntax and field names"
                }
            }
        }

    @staticmethod
    def opal_response(data: List[Dict[str, Any]], metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Wrap data in standard OPAL response format."""
        if metadata is None:
            metadata = {
                "recordCount": len(data),
                "queryTime": "1.234s",
                "region": "us-1"
            }
        
        return {
            "data": data,
            "metadata": metadata
        }

    @staticmethod
    def empty_response() -> Dict[str, Any]:
        """Generate empty response (no matching data)."""
        return {
            "data": [],
            "metadata": {
                "recordCount": 0,
                "queryTime": "0.456s",
                "region": "us-1"
            },
            "message": "No data found matching your query criteria"
        }


class MockEnvironments:
    """Container for different environment configurations."""
    
    @staticmethod
    def valid_environment() -> Dict[str, str]:
        """Valid environment configuration."""
        return {
            'OBSERVE_API_KEYS': json.dumps({
                "NA": "test_na_key_1234567890abcdef",
                "EU": "test_eu_key_fedcba0987654321"
            }),
            'OBSERVE_CUSTOMER_ID': 'test_customer_123',
            'OBSERVE_DATASET_IDS': '41000001,41000002,41000003'
        }

    @staticmethod
    def na_only_environment() -> Dict[str, str]:
        """Environment with only NA region access."""
        return {
            'OBSERVE_API_KEYS': json.dumps({
                "NA": "test_na_key_1234567890abcdef",
                "EU": ""
            }),
            'OBSERVE_CUSTOMER_ID': 'test_customer_456',
            'OBSERVE_DATASET_IDS': '41000004'
        }

    @staticmethod
    def missing_keys_environment() -> Dict[str, str]:
        """Environment missing API keys."""
        return {
            'OBSERVE_CUSTOMER_ID': 'test_customer_789',
            'OBSERVE_DATASET_IDS': '41000005'
        }

    @staticmethod
    def invalid_json_environment() -> Dict[str, str]:
        """Environment with invalid JSON in API keys."""
        return {
            'OBSERVE_API_KEYS': 'not-valid-json',
            'OBSERVE_CUSTOMER_ID': 'test_customer_999',
            'OBSERVE_DATASET_IDS': '41000006'
        }


class MockQueries:
    """Container for sample OPAL queries and expected results."""
    
    @staticmethod
    def basic_queries() -> Dict[str, Dict[str, Any]]:
        """Basic OPAL queries for testing."""
        return {
            "simple_limit": {
                "description": "Basic limit query",
                "pipeline": "limit 50",
                "expected_fields": [],
                "expected_limit": 50,
                "expected_offset": 0
            },
            "with_filter": {
                "description": "Filter with limit",
                "pipeline": 'filter message ~ "error" | limit 25',
                "expected_fields": [],
                "expected_limit": 25,
                "expected_offset": 0,
                "filter_term": "error",
                "filter_type": "message"
            },
            "with_fields": {
                "description": "Field selection with limit",
                "pipeline": "pick_col timestamp,message,level | limit 100",
                "expected_fields": ["timestamp", "message", "level"],
                "expected_limit": 100,
                "expected_offset": 0
            },
            "with_pagination": {
                "description": "Paginated query",
                "pipeline": "skip 50 | limit 25",
                "expected_fields": [],
                "expected_limit": 25,
                "expected_offset": 50
            },
            "complex_query": {
                "description": "Complex query with all features",
                "pipeline": 'pick_col timestamp,level,message,userId | filter level ~ "ERROR" | skip 100 | limit 25',
                "expected_fields": ["timestamp", "level", "message", "userId"],
                "expected_limit": 25,
                "expected_offset": 100,
                "filter_term": "ERROR",
                "filter_type": "level"
            }
        }

    @staticmethod
    def performance_test_queries() -> Dict[str, Dict[str, Any]]:
        """Queries for performance testing."""
        return {
            "small_fast": {
                "limit": 10,
                "expected_time_ms": 100,
                "description": "Small fast query"
            },
            "medium": {
                "limit": 100,
                "expected_time_ms": 500,
                "description": "Medium size query"
            },
            "large": {
                "limit": 1000,
                "expected_time_ms": 2000,
                "description": "Large query"
            },
            "max_limit": {
                "limit": 10000,
                "expected_time_ms": 10000,
                "description": "Maximum limit query"
            }
        }


class MockCurlResponses:
    """Container for mock curl responses in different scenarios."""
    
    @staticmethod
    def successful_response(data: Dict[str, Any]) -> tuple:
        """Mock successful curl response."""
        return (json.dumps(data), 0)  # (stdout, exit_code)

    @staticmethod
    def timeout_response() -> tuple:
        """Mock curl timeout response."""
        return ("curl: (28) Operation timed out", 28)

    @staticmethod
    def connection_failed_response() -> tuple:
        """Mock connection failed response."""
        return ("curl: (7) Failed to connect to host", 7)

    @staticmethod
    def http_error_response() -> tuple:
        """Mock HTTP error response."""
        return ("curl: (22) The requested URL returned error: 404", 22)

    @staticmethod
    def ssl_error_response() -> tuple:
        """Mock SSL certificate error response."""
        return ("curl: (60) SSL certificate verification failed", 60)

    @staticmethod
    def empty_response() -> tuple:
        """Mock empty response."""
        return ("", 0)


# Convenience functions for test setup
def get_mock_data() -> MockData:
    """Get MockData instance."""
    return MockData()

def get_mock_environments() -> MockEnvironments:
    """Get MockEnvironments instance."""
    return MockEnvironments()

def get_mock_queries() -> MockQueries:
    """Get MockQueries instance."""
    return MockQueries()

def get_mock_curl_responses() -> MockCurlResponses:
    """Get MockCurlResponses instance."""
    return MockCurlResponses()