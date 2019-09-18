"""The standalone runtime for individual correctness files."""

import argparse

from .resource import Executable
from grade.test.runner import Runner

MODES = ("parallel", "linear")


def main(runner: Runner):
    """Run all tests in the current file against a library."""

    parser = argparse.ArgumentParser(description="the command line interface for a standalone correctness file")
    parser.add_argument("--target")
    result = parser.parse_args()

    resources = {}
    if result.target:
        resources["target"] = Executable(*result.target.split())

    runner.run(**resources)
