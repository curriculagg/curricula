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

        single_parser = subparsers.add_parser("run")
        single_parser.add_argument("target", help="run tests on a single target")
        single_parser.add_argument("report", help="where to write the report to")

        batch_parser = subparsers.add_parser("batch")
        batch_parser.add_argument("targets", nargs="+", help="all targets to run")
        batch_parser.add_argument("reports", help="a directory to write reports to")

        summarize_parser = subparsers.add_parser("summarize")
        summarize_parser.add_argument("reports", help="the directory containing the grade reports")

    @classmethod
    def run(cls, parser: argparse.ArgumentParser, args: argparse.Namespace):
        """Start the grader."""

        options = vars(args)
        options.pop("app")

        grading_path = Path(options.pop("grading")).absolute()
        if not grading_path.is_dir():
            print("Grading artifact does not exist!", file=sys.stderr)
            exit(1)

        manager = Manager.load(grading_path)
        command = options.pop("command")

        if command == "run":
            output_path = Path(options.pop("report"))
            reports = manager.run(Path(options.pop("target")), **options)
            with output_path.open("w") as file:
                data = {problem_short: report.dump() for problem_short, report in reports.items()}
                json.dump(data, file, indent=2)

        elif command == "batch":
            output_path = Path(options.pop("reports"))
            output_path.mkdir(parents=True, exist_ok=True)
            for target_path, reports in manager.run_batch(map(Path, options.pop("targets")), **options):
                with output_path.joinpath(f"{target_path.parts[-1]}.json").open("w") as file:
                    data = {problem_short: report.dump() for problem_short, report in reports.items()}
                    json.dump(data, file, indent=2)

        elif command == "summarize":
            reports_path = Path(options.pop("reports"))
            summarize(grading_path, reports_path)
