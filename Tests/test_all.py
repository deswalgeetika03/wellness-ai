import sys
import unittest
from pathlib import Path


# Add the project root to Python's import path
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def run_query_pipeline_tests():
    from Tests import test_query_pipeline

    test_query_pipeline.main()


def run_query_pipeline_isolation_test():
    from Tests import test_query_pipeline

    test_query_pipeline.test_safety_route_isolation()


def suite():
    loader = unittest.TestLoader()

    test_suite = unittest.TestSuite()

    # Standard unittest-based test suites
    test_modules = [
        "Tests.test_retrieval",
        "Tests.test_api",
    ]

    for module in test_modules:
        test_suite.addTests(
            loader.loadTestsFromName(module)
        )

    # Existing manual end-to-end test suite
    test_suite.addTest(
        unittest.FunctionTestCase(
            run_query_pipeline_tests
        )
    )

    # Existing architectural isolation test
    test_suite.addTest(
        unittest.FunctionTestCase(
            run_query_pipeline_isolation_test
        )
    )

    return test_suite


if __name__ == "__main__":
    runner = unittest.TextTestRunner(
        verbosity=2
    )

    result = runner.run(suite())

    if not result.wasSuccessful():
        raise SystemExit(1)