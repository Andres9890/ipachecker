#!/usr/bin/env python3
"""
Test runner for ipachecker project.

This script runs all tests for the ipachecker project, including unit tests,
integration tests, and optional performance tests.
"""

import os
import sys
import unittest
import argparse
import coverage
from io import StringIO


def run_tests_with_coverage(test_pattern='test_*.py', coverage_report=True, html_report=False):
    """
    Run tests with coverage reporting.
    
    Args:
        test_pattern: Pattern to match test files
        coverage_report: Whether to print coverage report
        html_report: Whether to generate HTML coverage report
    
    Returns:
        TestResult object
    """
    # Initialize coverage
    cov = coverage.Coverage()
    cov.start()
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = 'tests'
    suite = loader.discover(start_dir, pattern=test_pattern)
    
    # Run tests with custom runner
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    
    # Stop coverage
    cov.stop()
    cov.save()
    
    # Print test results
    print(stream.getvalue())
    
    if coverage_report:
        print("\n" + "="*70)
        print("COVERAGE REPORT")
        print("="*70)
        cov.report(show_missing=True)
    
    if html_report:
        print("\nGenerating HTML coverage report...")
        cov.html_report(directory='htmlcov')
        print("HTML coverage report saved to 'htmlcov' directory")
    
    return result


def run_performance_tests():
    """Run performance tests for ipachecker."""
    print("Running performance tests...")
    
    # Import performance test modules here
    # from tests.test_performance import PerformanceTests
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add performance tests
    # suite.addTest(loader.loadTestsFromTestCase(PerformanceTests))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


def check_test_environment():
    """Check if the test environment is properly set up."""
    print("Checking test environment...")
    
    # Check if required dependencies are available
    required_packages = [
        'unittest',
        'coverage', 
        'requests_mock',
        'macholib'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing required packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    # Check if ipachecker module can be imported
    try:
        import ipachecker
        print(f"ipachecker module found (version: {ipachecker.__version__})")
    except ImportError:
        print("ipachecker module not found. Run 'pip install -e .' from project root.")
        return False
    
    # Check if test files exist
    test_files = [
        'tests/test_ipachecker.py',
        'tests/test_utils.py',
        'tests/constants.py'
    ]
    
    missing_files = []
    for test_file in test_files:
        if not os.path.exists(test_file):
            missing_files.append(test_file)
    
    if missing_files:
        print(f"Missing test files: {', '.join(missing_files)}")
        return False
    
    print("Test environment is properly set up")
    return True


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description='Run ipachecker tests')
    parser.add_argument('--pattern', default='test_*.py',
                        help='Test file pattern (default: test_*.py)')
    parser.add_argument('--no-coverage', action='store_true',
                        help='Skip coverage reporting')
    parser.add_argument('--html-coverage', action='store_true',
                        help='Generate HTML coverage report')
    parser.add_argument('--performance', action='store_true',
                        help='Run performance tests')
    parser.add_argument('--check-env', action='store_true',
                        help='Check test environment and exit')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')
    
    args = parser.parse_args()
    
    # Set up logging level
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    # Check environment if requested
    if args.check_env:
        if check_test_environment():
            sys.exit(0)
        else:
            sys.exit(1)
    
    # Check environment before running tests
    if not check_test_environment():
        print("Test environment check failed. Use --check-env for details.")
        sys.exit(1)
    
    print("Starting ipachecker test suite...")
    print("="*70)
    
    # Run main tests
    if args.no_coverage:
        # Run without coverage
        loader = unittest.TestLoader()
        suite = loader.discover('tests', pattern=args.pattern)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
    else:
        # Run with coverage
        result = run_tests_with_coverage(
            test_pattern=args.pattern,
            coverage_report=True,
            html_report=args.html_coverage
        )
    
    # Run performance tests if requested
    if args.performance:
        print("\n" + "="*70)
        perf_result = run_performance_tests()
        # Combine results (simplified)
        result.testsRun += perf_result.testsRun
        result.failures.extend(perf_result.failures)
        result.errors.extend(perf_result.errors)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(getattr(result, 'skipped', []))
    passed = total_tests - failures - errors - skipped
    
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed}")
    print(f"Failed: {failures}")
    print(f"Errors: {errors}")
    print(f"Skipped: {skipped}")
    
    if failures > 0:
        print(f"\n{failures} test(s) failed:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if errors > 0:
        print(f"\n{errors} test(s) had errors:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    if failures == 0 and errors == 0:
        print("\nAll tests passed!")
        success_rate = (passed / total_tests) * 100 if total_tests > 0 else 0
        print(f"Success rate: {success_rate:.1f}%")
    
    # Exit with appropriate code
    sys.exit(0 if failures == 0 and errors == 0 else 1)


if __name__ == '__main__':
    main()