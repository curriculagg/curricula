import argparse

from .build.plugin import BuildPlugin
from .grade.plugin import GradePlugin
from .library.log import add_logging_arguments, handle_logging_arguments

PLUGINS = (BuildPlugin, GradePlugin)


parser = argparse.ArgumentParser(prog="curricula", description="Command line interface for Curricula")
add_logging_arguments(parser)

subparsers = parser.add_subparsers(required=True, dest="app")
for plugin in PLUGINS:
    plugin.setup(subparsers.add_parser(plugin.name, help=plugin.help))

args = parser.parse_args()
if handle_logging_arguments(args) != 0:
    exit(1)

status = {plugin.name: plugin.main for plugin in PLUGINS}[args.app](parser, args)
exit(status)
