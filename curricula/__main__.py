import argparse

from .build import parser as build
from .grade import parser as grade


parser = argparse.ArgumentParser(prog="curricula", description="Command line interface for Curricula")
subparsers = parser.add_subparsers(required=True, dest="app")

build.setup(subparsers.add_parser("build", help="Run the material builder", ))
grade.setup(subparsers.add_parser("grade", help="Manage assignment grading for submissions"))

args = vars(parser.parse_args())
dict(build=build.run, grade=grade.run)[args.pop("app")](args)
