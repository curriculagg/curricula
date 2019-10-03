import argparse
from pathlib import Path

from . import build


def setup(parser: argparse.ArgumentParser):
    """Create a subparser for the build app."""

    parser.add_argument("material", help="Path to the root material directory")
    parser.add_argument("-a", "--assignment", nargs=1, dest="assignment", help="A specific assignment to build")


def run(parser: argparse.ArgumentParser, args: argparse.Namespace):
    """Run if the build app is chosen."""

    material_path = Path(args.material).absolute()
    build.build(material_path, **vars(args))
