"""The standalone runtime for individual test files."""

import argparse
import ctypes

from grade.test.testing import tests


def main():
    """Run all tests in the current file against a library."""

    parser = argparse.ArgumentParser(description="the command line interface for a standalone test file")
    parser.add_argument("library", help="the compiled grading binary for the problem")
    result = parser.parse_args()

    library = ctypes.cdll.LoadLibrary(result.library)
    tests.run(library)
