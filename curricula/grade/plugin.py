import argparse
import json
from pathlib import Path
from contextlib import contextmanager
from typing import TextIO, Dict, Iterable

from .manager import Manager
from .report import Report
from .tools.summarize import summarize
from .tools.format import format_report_markdown
from .tools.compare import compare_output
from ..plugin import Plugin, PluginException


def make_report_name(target_path: Path, extension: str) -> str:
    """Generate a report file name."""

    return f"{target_path.parts[-1]}.report.{extension}"


def change_extension(report_path: Path, extension: str) -> str:
    """Return the report name with a different extension."""

    basename = report_path.parts[-1].rsplit(".", maxsplit=1)[0]
    return f"{basename}.{extension}"


def dump_reports(reports: Dict[str, Report], file: TextIO):
    """Write a dict of reports to a file."""

    data = {problem_short: report.dump() for problem_short, report in reports.items()}
    json.dump(data, file, indent=2)


@contextmanager
def file_from_options(options: dict, default_file_name: str, *, batch: bool) -> TextIO:
    """Return an open file and whether to close it after."""

    if options["file"] is not None:
        if batch:
            raise PluginException("Cannot use --file for batch grading, use --directory")
        output_path = Path(options.pop("file"))
        if not output_path.parent.exists():
            raise PluginException(f"Containing directory {output_path.parent} does not exist")
        with output_path.open("w") as file:
            yield file
    elif options["directory"] is not None:
        output_path = Path(options.pop("directory")).joinpath(default_file_name)
        with output_path.open("w") as file:
            yield file
    else:
        raise PluginException("Output file or directory must be specified!")


class GradePlugin(Plugin):
    """Implement grade plugin."""

    name = "grade"
    help = "Manage assignment grading for submissions"

    @classmethod
    def setup(cls, parser: argparse.ArgumentParser):
        """Setup argument parser for grade command."""

        parser.add_argument("grading", help="built grading directory artifact")
        parser.add_argument("-v", "--verbosity", action="count", default=0)
        subparsers = parser.add_subparsers(required=True, dest="command")

        run_parser = subparsers.add_parser("run")
        run_parser.add_argument("-q", "--quiet", action="store_true", help="whether to log test results")
        to_group = run_parser.add_mutually_exclusive_group(required=True)
        to_group.add_argument("-f", "--file", help="output file for single report")
        to_group.add_argument("-d", "--directory", help="where to write reports to if batched")
        run_parser.add_argument("targets", nargs="+", help="run tests on a single target")

        format_parser = subparsers.add_parser("format")
        to_group = format_parser.add_mutually_exclusive_group(required=True)
        to_group.add_argument("-f", "--file", help="output file for single report")
        to_group.add_argument("-d", "--directory", help="where to write reports to if batched")
        format_parser.add_argument("template", help="the markdown template to write the report to")
        format_parser.add_argument("reports", nargs="+", help="a variable number of reports to format")

        summarize_parser = subparsers.add_parser("summarize")
        summarize_parser.add_argument("reports", help="the directory containing the grade reports")
        
        compare_parser = subparsers.add_parser("compare")
        to_group = compare_parser.add_mutually_exclusive_group(required=True)
        to_group.add_argument("-f", "--file", help="output file for single report")
        to_group.add_argument("-d", "--directory", help="where to write reports to if batched")
        compare_parser.add_argument("report", help="the report to compare")

    @classmethod
    def main(cls, parser: argparse.ArgumentParser, args: argparse.Namespace):
        """Start the grader."""

        options = vars(args)
        options.pop("app")

        grading_path = Path(options.pop("grading")).absolute()
        if not grading_path.is_dir():
            raise PluginException("Grading artifact does not exist!")

        {
            "run": cls.run,
            "format": cls.format,
            "summarize": cls.summarize,
            "compare": cls.compare,
        }[options.pop("command")](grading_path, options)

    @classmethod
    def run(cls, grading_path: Path, options: dict):
        """Do a single grade report."""

        if len(options["targets"]) == 1:
            target_path = Path(options.pop("targets")[0])
            cls.run_single(grading_path, target_path, options)
        else:
            cls.run_batch(grading_path, map(Path, options.pop("targets")), options)

    @classmethod
    def run_single(cls, grading_path: Path, target_path: Path, options: dict):
        """Grade a single file, write to file output."""

        manager = Manager.load(grading_path)
        reports = manager.run_single(target_path, **options)
        with file_from_options(options, make_report_name(target_path, "json"), batch=False) as file:
            dump_reports(reports, file)

    @classmethod
    def run_batch(cls, grading_path: Path, target_paths: Iterable[Path], options: dict):
        """Run a batch of reports."""

        manager = Manager.load(grading_path)
        for target_path, reports in manager.run_batch(target_paths, **options):
            with file_from_options(options, make_report_name(target_path, "json"), batch=True) as file:
                dump_reports(reports, file)

    @classmethod
    def format(cls, grading_path: Path, options: dict):
        """Format a bunch of reports."""

        template_path = Path(options.pop("template"))
        if len(options["reports"]) == 1:
            report_path = Path(options.pop("reports")[0])
            cls.format_single(grading_path, template_path, report_path, options)
        else:
            cls.format_batch(grading_path, template_path, map(Path, options.pop("reports")), options)

    @classmethod
    def format_single(cls, grading_path: Path, template_path: Path, report_path: Path, options: dict):
        """Format a single report."""

        with file_from_options(options, change_extension(report_path, "md"), batch=False) as file:
            file.write(format_report_markdown(grading_path, template_path, report_path))

    @classmethod
    def format_batch(cls, grading_path: Path, template_path: Path, report_paths: Iterable[Path], options: dict):
        """Format a batch of results."""

        for report_path in report_paths:
            cls.format_single(grading_path, template_path, report_path, options)

    @classmethod
    def summarize(cls, grading_path: Path, options: dict):
        """Summarize a batch of reports."""

        reports_path = Path(options.pop("reports"))
        summarize(grading_path, reports_path)

    @classmethod
    def compare(cls, grading_path: Path, options: dict):
        """Generate a comparison of two files."""

        report_path = Path(options.pop("report"))
        with file_from_options(options, change_extension(report_path, "compare.html"), batch=False) as file:
            file.write(compare_output(report_path))
