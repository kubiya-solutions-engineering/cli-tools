"""
Test runner and test suite validation.
Provides utilities for running the complete test suite and validating test coverage.
"""
import pytest
import subprocess
import sys
import os
from pathlib import Path


def run_unit_tests():
    """Run unit tests only."""
    return pytest.main([
        "-v",
        "-m", "unit",
        "tests/test_opal_query_construction.py"
    ])


def run_integration_tests():
    """Run integration tests only."""
    return pytest.main([
        "-v", 
        "-m", "integration",
        "tests/test_integration.py"
    ])


def run_performance_tests():
    """Run performance tests only."""
    return pytest.main([
        "-v",
        "-m", "performance", 
        "tests/test_performance.py"
    ])


def run_all_tests():
    """Run the complete test suite."""
    return pytest.main([
        "-v",
        "--cov=observe_cli_tools",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "tests/"
    ])


def validate_test_environment():
    """Validate that the test environment is properly configured."""
    print("🔍 Validating test environment...")
    
    # Check required dependencies
    required_packages = ['pytest', 'pytest-mock', 'pytest-cov', 'responses']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} is available")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"💡 Install missing packages: pip install {' '.join(missing_packages)}")
        return False
    
    # Check test files exist
    test_files = [
        'tests/test_opal_query_construction.py',
        'tests/test_integration.py', 
        'tests/test_pagination_and_errors.py',
        'tests/test_performance.py',
        'tests/conftest.py',
        'tests/fixtures.py'
    ]
    
    missing_files = []
    project_root = Path(__file__).parent.parent
    
    for test_file in test_files:
        file_path = project_root / test_file
        if file_path.exists():
            print(f"✅ {test_file} exists")
        else:
            missing_files.append(test_file)
            print(f"❌ {test_file} is missing")
    
    if missing_files:
        print(f"💡 Missing test files: {missing_files}")
        return False
    
    # Check shell environment
    required_commands = ['bash', 'jq']
    for command in required_commands:
        result = subprocess.run(['which', command], capture_output=True)
        if result.returncode == 0:
            print(f"✅ {command} is available")
        else:
            print(f"⚠️  {command} is not available (some tests may be skipped)")
    
    print("✅ Test environment validation completed")
    return True


def generate_test_report():
    """Generate a comprehensive test report."""
    print("📊 Generating test report...")
    
    # Run tests with detailed output
    result = pytest.main([
        "-v",
        "--tb=long",
        "--cov=observe_cli_tools",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml",
        "--junit-xml=test-results.xml",
        "tests/"
    ])
    
    if result == 0:
        print("✅ All tests passed!")
        print("📋 Test reports generated:")
        print("   - HTML coverage: htmlcov/index.html")
        print("   - XML coverage: coverage.xml") 
        print("   - JUnit XML: test-results.xml")
    else:
        print("❌ Some tests failed. Check the output above for details.")
    
    return result


def main():
    """Main test runner entry point."""
    if len(sys.argv) < 2:
        print("Usage: python test_runner.py [validate|unit|integration|performance|all|report]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "validate":
        if not validate_test_environment():
            sys.exit(1)
    
    elif command == "unit":
        sys.exit(run_unit_tests())
    
    elif command == "integration": 
        sys.exit(run_integration_tests())
    
    elif command == "performance":
        sys.exit(run_performance_tests())
    
    elif command == "all":
        sys.exit(run_all_tests())
    
    elif command == "report":
        sys.exit(generate_test_report())
    
    else:
        print(f"Unknown command: {command}")
        print("Available commands: validate, unit, integration, performance, all, report")
        sys.exit(1)


if __name__ == "__main__":
    main()