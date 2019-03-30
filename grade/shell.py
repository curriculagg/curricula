"""The standalone runtime for individual correctness files."""

import argparse
import os

from .manager import Manager

MODES = ("parallel", "linear")


def main(manager: Manager):
    """Run all tests in the current file against a library."""

    parser = argparse.ArgumentParser(description="the command line interface for a standalone correctness file")
    parser.add_argument("-m", "--mode", help="parallelization options", default="parallel", choices=MODES)
    args = parser.parse_args()

    target = Target(os.path.abspath(args.binary))

    if args.mode == "parallel":
        from grade.extension import ParallelRunner
        runner = ParallelRunner()
    elif args.mode == "linear":
        runner = Runner()
    else:
        return

    runner.load(manager.tests)
    runner.run(target)
