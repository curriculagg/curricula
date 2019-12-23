import argparse

from .build.plugin import BuildPlugin
from .grade.plugin import GradePlugin

PLUGINS = (BuildPlugin, GradePlugin)


parser = argparse.ArgumentParser(prog="curricula", description="Command line interface for Curricula")
subparsers = parser.add_subparsers(required=True, dest="app")
for plugin in PLUGINS:
    plugin.setup(subparsers.add_parser(plugin.name, help=plugin.help))

args = parser.parse_args()

status = {plugin.name: plugin.main for plugin in PLUGINS}[args.app](parser, args)
exit(status)
