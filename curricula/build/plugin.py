import sys
import argparse
import jsonschema
from pathlib import Path

from . import build
from ..plugin import Plugin
from ..core.validate import validate
from ..library.log import add_logging_arguments, handle_logging_arguments


class BuildPlugin(Plugin):
    """Plugin for the build subsystem."""

    name = "build"
    help = "Run the material builder"

    @classmethod
    def setup(cls, parser: argparse.ArgumentParser):
        """Create a subparser for the build app."""

        parser.add_argument("assignment", help="Path to the root material directory")
        parser.add_argument("-c", "--check", dest="check", action="store_true", help="Only check")
        add_logging_arguments(parser)

    @classmethod
    def main(cls, parser: argparse.ArgumentParser, args: argparse.Namespace):
        """Run if the build app is chosen."""

        handle_logging_arguments(parser, args)

        options = vars(args)
        options.pop("app")

        assignment_path = Path(options.pop("assignment")).absolute()
        artifacts_path = Path().joinpath("artifacts").joinpath(assignment_path.parts[-1])

        try:
            validate(assignment_path)
        except jsonschema.ValidationError:
            return
        if options.pop("check"):
            return

        try:
            build.build(assignment_path, artifacts_path, **options)
        except ValueError as exception:
            print(f"Build error: {exception}", file=sys.stderr)
            exit(1)
