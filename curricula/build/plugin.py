import sys
import argparse
from pathlib import Path

from . import build
from ..plugin import Plugin
from ..mapping.validate import validate


class BuildPlugin(Plugin):
    """Plugin for the build subsystem."""

    name = "build"
    help = "Run the material builder"

    @classmethod
    def setup(cls, parser: argparse.ArgumentParser):
        """Create a subparser for the build app."""

        parser.add_argument("material", help="Path to the root material directory")
        parser.add_argument("-a", "--assignment", nargs=1, dest="assignment", help="A single assignment to build")
        parser.add_argument("-v", "--validate", dest="validate", action="store_true", help="Only validate")

    @classmethod
    def run(cls, parser: argparse.ArgumentParser, args: argparse.Namespace):
        """Run if the build app is chosen."""

        options = vars(args)
        material_path = Path(options.pop("material")).absolute()
        validate(material_path)

        if options.pop("validate"):
            return

        try:
            build.build(material_path, **options)
        except ValueError as exception:
            print(f"Build error: {exception}", file=sys.stderr)
            exit(1)
