import argparse
import jsonschema
from pathlib import Path

from . import build
from .validate import validate
from ..plugin import Plugin
from ..library.log import log


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

    @classmethod
    def main(cls, parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
        """Run if the build app is chosen."""

        options = vars(args)
        options.pop("app")
        assignment_path = Path(options.pop("assignment"))

        # Sanity check
        if not assignment_path.is_dir():
            log.error("assignment path does not exist!")
            return 1

        # If no explicit destination, put inside a custom artifacts directory
        if options["destination"]:
            artifacts_path = Path(options.pop("destination"))
        else:
            artifacts_path = Path().joinpath("artifacts", assignment_path.parts[-1])
            options.pop("destination")

        # Nest inside directory if flagged
        if options.pop("inside"):
            artifacts_path = artifacts_path.joinpath(assignment_path.parts[-1])

        # Validate the assignments and problems, return if only checking
        try:
            validate(assignment_path)
        except jsonschema.ValidationError:
            return 1
        if options.pop("check"):
            return 0

        build.build(assignment_path, artifacts_path, **options)
        return 0
