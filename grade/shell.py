"""The standalone runtime for individual correctness files."""

import argparse
import json
from pathlib import Path

from .grader import Grader
from .resource import Context

MODES = ("parallel", "linear")


def main(grader: Grader):
    """Run all tests in the current file against a library."""

    parser = argparse.ArgumentParser(description="the command line interface for a standalone correctness file")
    parser.add_argument("target", help="typically the submission directory to test")
    parser.add_argument("destination", help="the directory or file to write the report to", default=".")

    result = vars(parser.parse_args())
    destination = Path(result.pop("destination"))
    context = Context(Path(result.pop("target")).absolute(), result)

    report = grader.run(context=context)

    if destination.is_dir():
        path = str(destination.joinpath(f"{context.target.parts[-1]}.report.json"))
    else:
        path = str(destination)

    with open(path, "w") as file:
        json.dump(report.dump(), file, indent=2)
