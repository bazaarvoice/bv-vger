import unittest

# Import test modules
from statistics.git import test_git_pull_requests

# Initialize test suites
loader = unittest.TestLoader()
suite  = unittest.TestSuite()

# Add tests to the test suite
suite.addTests(loader.loadTestsFromModule(test_git_pull_requests))

# Run tests
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)