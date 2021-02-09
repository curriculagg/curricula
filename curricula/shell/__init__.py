import argparse
import logging

from .plugin import Plugin, PluginDispatcher
from ..log import log


class Curricula(PluginDispatcher):
    """Aggregate all known plugins."""

    name = "command"
    help = "the subcommand corresponding to the desired module"
    plugins = (
        Plugin.find("curricula_grade", "grade"),
        Plugin.find("curricula_compile", "compile"),
        Plugin.find("curricula_format", "format"))


def main() -> int:
    """Create the parser."""

    parser = argparse.ArgumentParser(prog="curricula", description="Command line interface for Curricula")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true", default=False)
    group.add_argument("-q", "--quiet", action="store_true", default=False)
    parser.add_argument("-l", "--log", default=None)

    curricula = Curricula()
    curricula.setup(parser)

    args = vars(parser.parse_args())
    if args["verbose"]:
        log.setLevel(logging.DEBUG)
    elif args["quiet"]:
        log.setLevel(logging.WARNING)

    if args["log"]:
        handler_stream = logging.FileHandler(args["log"])
        log.addHandler(handler_stream)

    return curricula.main(parser, args)
