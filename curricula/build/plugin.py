import argparse
import jsonschema
import logging
from pathlib import Path

from . import build
from ..plugin import Plugin
from ..core.validate import validate
from ..library.log import add_logging_arguments, handle_logging_arguments

log = logging.getLogger("curricula")


class BuildPlugin(Plugin):
    """Plugin for the build subsystem."""

    name = "build"
    help = "Run the material builder"

    @classmethod
    def setup(cls, parser: argparse.ArgumentParser):
        """Create a subparser for the build app."""

        parser.add_argument("assignment", help="path to the assignment directory")
        parser.add_argument("-c", "--check", action="store_true", help="only check JSON manifests")
        parser.add_argument("-d", "--destination", help="a directory to write the artifacts to")
        parser.add_argument("-i", "--inside", action="store_true", help="make the artifacts directory in destination")
        add_logging_arguments(parser)

    @classmethod
    def main(cls, parser: argparse.ArgumentParser, args: argparse.Namespace):
        """Run if the build app is chosen."""

        handle_logging_arguments(parser, args)

        options = vars(args)
        options.pop("app")
        assignment_path = Path(options.pop("assignment"))
        artifacts_path = Path(options.pop("destination"))
        if options.pop("inside"):
            artifacts_path = artifacts_path.joinpath(assignment_path.parts[-1])

        try:
            validate(assignment_path)
        except jsonschema.ValidationError:
            return
        if options.pop("check"):
            return

        try:
            build.build(assignment_path, artifacts_path, **options)
        except ValueError as exception:
            log.error(exception)
            exit(1)
