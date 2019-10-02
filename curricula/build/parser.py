import argparse
from pathlib import Path

from . import build


def setup(parser: argparse.ArgumentParser):
    """Create a subparser for the build app."""

    parser.add_argument("material", help="Path to the root material directory")
    parser.add_argument("-a", "--assignment", nargs=1, dest="assignment", help="A specific assignment to build")
    parser.add_argument("-p", "--problem", nargs=1, dest="problem", help="A problem in the assignment to build")


def run(parser: argparse.ArgumentParser, args: argparse.Namespace):
    """Run if the build app is chosen."""

    if args.problem is not None and args.assignment is None:
        parser.error("You must specify an assignment to build a specific problem!")

    build.build(vars(args))
