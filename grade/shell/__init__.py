"""The standalone runtime for individual correctness files."""

import argparse
import json
from pathlib import Path

from ..grader import Grader
from ..resource import Context
from .summarize import summarize

MODES = ("parallel", "linear")


def single(grader: Grader, args: dict):
    """Run tests on a single target and print report."""

    context = Context(Path(args.pop("target")).absolute(), args)
    report = grader.run(context=context)
    print(json.dumps(report.dump(), indent=2))


def main(grader: Grader):
    """Run all tests in the current file against a library."""

    parser = argparse.ArgumentParser(description="the command line interface for a grade test file")
    subparsers = parser.add_subparsers(required=True, dest="command")

    single_parser = subparsers.add_parser("single")
    single_parser.add_argument("target", help="run tests on a single target")

    summarize_parser = subparsers.add_parser("summarize")
    summarize_parser.add_argument("reports", help="the directory containing the grade reports")

    args = vars(parser.parse_args())
    command = args.pop("command")
    if command == "single":
        single(grader, args)
    elif command == "summarize":
        summarize(grader, args)
