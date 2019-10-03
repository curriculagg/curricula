import argparse
from pathlib import Path

from . import build
from ..plugin import Plugin


class BuildPlugin(Plugin):
    """Plugin for the build subsystem."""

    name = "build"
    help = "Run the material builder"

    @classmethod
    def setup(cls, parser: argparse.ArgumentParser):
        """Create a subparser for the build app."""

        parser.add_argument("material", help="Path to the root material directory")
        parser.add_argument("-a", "--assignment", nargs=1, dest="assignment", help="A specific assignment to build")

    @classmethod
    def run(cls, parser: argparse.ArgumentParser, args: argparse.Namespace):
        """Run if the build app is chosen."""

        material_path = Path(args.material).absolute()
        build.build(material_path, **vars(args))
