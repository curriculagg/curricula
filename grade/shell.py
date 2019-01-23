"""The standalone runtime for individual test files."""

import argparse
import os

from .test import Target, Manager, Runner

MODES = ("parallel", "linear")


def main(manager: Manager):
    """Run all tests in the current file against a library."""

    parser = argparse.ArgumentParser(description="the command line interface for a standalone test file")
    parser.add_argument("binary", help="the compiled grading binary for the problem")
    parser.add_argument("-m", "--mode", help="parallelization options", default="parallel", choices=MODES)
    args = parser.parse_args()

    target = Target(os.path.abspath(args.binary))

    if args.mode == "parallel":
        from .test.extension.parallel import ParallelRunner
        runner = ParallelRunner()
    elif args.mode == "linear":
        runner = Runner()
    else:
        return

    runner.load(manager.tests)
    runner.run(target)
