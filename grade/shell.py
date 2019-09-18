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
    parser.add_argument("target")

    result = vars(parser.parse_args())
    context = Context(Path(result.pop("target")).absolute(), result)

    report = grader.run(context=context)
    with open("report.json", "w") as file:
        json.dump(report.dump(), file, indent=2)
