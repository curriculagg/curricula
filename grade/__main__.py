"""The command line interface for the Grade library.

This script allows graders to include multiple files containing test
cases for a problem set. This circumvents having to duplicate tests
for students and graders; students can be given access to a set of
base cases and graders can be given different cases to run alongside.

https://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
https://stackoverflow.com/questions/252417/how-can-i-use-a-dll-file-from-python
"""


import argparse
import ctypes
import importlib.util

from .testing import tests


def load_module(path):
    """Shorthand for importing a module."""

    spec = importlib.util.spec_from_file_location("tests", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


parser = argparse.ArgumentParser(description="the command line interface for the combined grader")
parser.add_argument("tests", nargs="+", help="one or more paths to each test file")
parser.add_argument("library", help="the compiled grading binary for the problem")
result = parser.parse_args()

for path in result.tests:
    load_module(path)

library = ctypes.cdll.LoadLibrary(result.library)
tests.run(library)
