"""The standalone runtime for individual test files."""

import argparse
import os

from grade.test import Target, run


def main():
    """Run all tests in the current file against a library."""

    parser = argparse.ArgumentParser(description="the command line interface for a standalone test file")
    parser.add_argument("binary", help="the compiled grading binary for the problem")
    result = parser.parse_args()

    target = Target(os.path.abspath(result.binary))
    run(target)
