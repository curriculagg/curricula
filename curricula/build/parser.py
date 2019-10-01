import argparse
from pathlib import Path

from . import build


def setup(parser: argparse.ArgumentParser):
    """Create a subparser for the build app."""

    parser.add_argument("path")


def run(args: dict):
    """Run if the build app is chosen."""

    build.build(Path(args["path"]))
