import argparse
import json
import sys
from pathlib import Path

from .grader import Grader
from .manager import Manager
from .resource import Context
from .shell.summarize import summarize
from ..plugin import Plugin

MODES = ("parallel", "linear")


def single(grader: Grader, args: dict):
    """Run tests on a single target and print report."""

    context = Context(Path(args.pop("target")).absolute(), args)
    report = grader.run(context=context)
    with Path(args.pop("report")).open("w") as file:
        json.dump(report.dump(), file, indent=2)


class GradePlugin(Plugin):
    """Implement grade plugin."""

    name = "grade"
    help = "Manage assignment grading for submissions"

    @classmethod
    def setup(cls, parser: argparse.ArgumentParser):
        """Setup argument parser for grade command."""

        parser.add_argument("grading", help="built grading directory artifact")
        subparsers = parser.add_subparsers(required=True, dest="command")

        single_parser = subparsers.add_parser("single")
        single_parser.add_argument("target", help="run tests on a single target")
        single_parser.add_argument("report", help="where to write the report to")

        batch_parser = subparsers.add_parser("batch")

        summarize_parser = subparsers.add_parser("summarize")
        summarize_parser.add_argument("reports", help="the directory containing the grade reports")

    @classmethod
    def run(cls, parser: argparse.ArgumentParser, args: argparse.Namespace):
        """Start the grader."""

        options = vars(args)

        grading_path = Path(options.pop("grading")).absolute()
        if not grading_path.is_dir():
            print("Grading artifact does not exist!", file=sys.stderr)
            exit(1)

        manager = Manager.load(grading_path)
        command = options.pop("command")
