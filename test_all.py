"""Runs all test files for all classes"""

import unittest
from testing_modules.test_database import TestDataBase
from testing_modules.test_ILC import TestILC


# test_cases = (TestState, TestDataBase, TestILC)
test_cases = (TestDataBase, TestILC)


def load_all_tests():

    # Load test suite
    suite = unittest.TestSuite()

    # Load test loader
    loader = unittest.TestLoader()

    # Iterate over test cases
    for test_class in test_cases:

        # Load all tests from test classes
        tests = loader.loadTestsFromTestCase(test_class)

        # Add test to test suite
        suite.addTests(tests)

    # Return test suite
    return suite


if __name__ == '__main__':

    # Load text for of test runner
    runner = unittest.TextTestRunner()

    # Run all tests in all test classes
    runner.run(load_all_tests())
