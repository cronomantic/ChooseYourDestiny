#!/usr/bin/env python3
"""
Complete regression test suite runner for ChooseYourDestiny compiler.

This script runs all test categories:
- Lexer tests (tokenization and lexical analysis)
- Parser tests (syntax analysis and grammar validation)
- Integration tests (end-to-end compilation pipeline)

Usage:
    python run_tests.py                 # Run all tests
    python run_tests.py -v              # Verbose output
    python run_tests.py test_lexer      # Run specific test module
    python run_tests.py -k test_strict  # Run tests matching pattern
    python run_tests.py --coverage      # Generate coverage report (requires coverage package)
"""

import sys
import unittest
from pathlib import Path
import argparse

# Add tests directory to path
TESTS_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(TESTS_DIR))

# Add src to path
sys.path.insert(0, str(TESTS_DIR.parent / "src" / "cydc"))


def discover_tests(pattern=None):
    """
    Discover all tests in the tests directory.
    
    Args:
        pattern: Optional pattern to filter test names
        
    Returns:
        TestSuite with discovered tests
    """
    loader = unittest.TestLoader()
    
    if pattern:
        # If pattern provided, search for matching tests
        suite = loader.discover(
            start_dir=str(TESTS_DIR),
            pattern=f"{pattern}.py"
        )
    else:
        # Discover all test_*.py files
        suite = loader.discover(
            start_dir=str(TESTS_DIR),
            pattern="test_*.py"
        )
    
    return suite


def run_with_coverage(suite):
    """
    Run tests with coverage analysis.
    
    Args:
        suite: TestSuite to run
        
    Returns:
        TestResult
    """
    try:
        import coverage
    except ImportError:
        print("Coverage package not installed. Install with: pip install coverage")
        return None
    
    # Start coverage
    cov = coverage.Coverage()
    cov.start()
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Stop coverage and report
    cov.stop()
    cov.save()
    
    print("\n" + "="*70)
    print("COVERAGE REPORT")
    print("="*70)
    cov.report(include=["*/src/cydc/cydc/*"])
    
    return result


def print_header():
    """Print test suite header."""
    print("="*70)
    print("ChooseYourDestiny Compiler - Regression Test Suite")
    print("="*70)
    print()


def print_summary(result):
    """Print test execution summary."""
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run:     {result.testsRun}")
    print(f"Failures:      {len(result.failures)}")
    print(f"Errors:        {len(result.errors)}")
    print(f"Skipped:       {len(result.skipped)}")
    
    if result.wasSuccessful():
        try:
            print("\n[OK] ALL TESTS PASSED")
        except:
            print("\nALL TESTS PASSED")
    else:
        try:
            print("\n[FAILED] SOME TESTS FAILED")
        except:
            print("\nSOME TESTS FAILED")
    
    print("="*70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run regression test suite for ChooseYourDestiny compiler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all tests
  python run_tests.py -v                 # Verbose mode
  python run_tests.py test_lexer         # Run lexer tests only
  python run_tests.py test_parser        # Run parser tests only
  python run_tests.py test_integration   # Run integration tests only
  python run_tests.py -k strict          # Run tests containing 'strict'
  python run_tests.py --coverage         # Run with coverage analysis
        """
    )
    
    parser.add_argument(
        "pattern",
        nargs="?",
        help="Pattern to match test module names (e.g., test_lexer, test_parser)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "-k", "--keyword",
        help="Pattern for test names to run (e.g., 'strict' runs all tests with 'strict' in the name)"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--failfast",
        action="store_true",
        help="Stop on first failure"
    )
    
    args = parser.parse_args()
    
    print_header()
    
    # Discover tests
    if args.pattern:
        print(f"Discovering tests matching: {args.pattern}")
        suite = discover_tests(pattern=args.pattern)
    else:
        print("Discovering all tests...")
        suite = discover_tests()
    
    # Filter by keyword if provided
    if args.keyword:
        print(f"Filtering tests by keyword: {args.keyword}")
        filtered_suite = unittest.TestSuite()
        
        def filter_tests(test_group):
            for test in test_group:
                if isinstance(test, unittest.TestSuite):
                    filter_tests(test)
                else:
                    if args.keyword.lower() in str(test).lower():
                        filtered_suite.addTest(test)
        
        filter_tests(suite)
        suite = filtered_suite
    
    print(f"Running test suite...\n")
    
    # Run tests
    if args.coverage:
        result = run_with_coverage(suite)
        if result is None:
            return 1
    else:
        verbosity = 2 if args.verbose else 1
        runner = unittest.TextTestRunner(verbosity=verbosity, failfast=args.failfast)
        result = runner.run(suite)
    
    # Print summary
    print_summary(result)
    
    # Return appropriate exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
