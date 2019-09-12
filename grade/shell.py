"""The standalone runtime for individual correctness files."""

import argparse

from .manager import Manager
from .resource import Executable
from .runner import Runner

MODES = ("parallel", "linear")


def main(manager: Manager):
    """Run all tests in the current file against a library."""

    parser = argparse.ArgumentParser(description="the command line interface for a standalone correctness file")
    parser.add_argument("--target")
    result = parser.parse_args()

    resources = {}
    if result.target:
        resources["target"] = Executable(*result.target.split())

    runner = Runner()
    runner.load(manager.tests)
    runner.run(**resources)
