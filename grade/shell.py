"""The standalone runtime for individual correctness files."""

import argparse
from pathlib import Path

from .resource import Context
from .test.runner import Runner

MODES = ("parallel", "linear")


def main(runner: Runner):
    """Run all tests in the current file against a library."""

    parser = argparse.ArgumentParser(description="the command line interface for a standalone correctness file")
    parser.add_argument("target")
    result = vars(parser.parse_args())
    context = Context(Path(result.pop("target")).absolute(), result)
    runner.run(context=context)
