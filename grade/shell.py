"""The standalone runtime for individual correctness files."""

import argparse

from .manager import Manager
from .runner import Runner

MODES = ("parallel", "linear")


def main(manager: Manager):
    """Run all tests in the current file against a library."""

    parser = argparse.ArgumentParser(description="the command line interface for a standalone correctness file")
    # parser.add_argument("-m", "--mode", help="parallelization options", default="parallel", choices=MODES)
    args = parser.parse_args()

    runner = Runner()
    runner.load(manager.tests)
    runner.run()
