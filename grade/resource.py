import os
from typing import Optional, Tuple

from .library.process import Runtime, run


class Resource:
    """A resource required for a test."""

    def check(self):
        """Check whether the resource may be used."""


class File(Resource):
    """A resource corresponding to a file."""

    path: str

    def __init__(self, path: Optional[str]):
        """Require a path to exist."""

        self.path = path

    def check(self):
        """Assert the file exists."""

        assert os.path.exists(self.path), "file does not exist"


class Executable(Resource):
    """A runnable testing target program."""

    args: Tuple[str]
    paths: Tuple[str]

    def __init__(self, *args: str, path: str = None, paths: Tuple[str] = None):
        """Initialize a target with commands to run the target.

        Any paths invoked in the executable command must be absolute; relative
        requires subprocess configuration that is unsafe. File paths to check
        for validation may be relative, however.
        """

        self.args = tuple(args)
        self.paths = tuple(filter(None, tuple(path) + paths))

    def check(self):
        """Assert the associated executable files exists."""

        for path in self.paths:
            assert path is None or os.path.exists(path), "executable file does not exist"

    def run(self, *args: str, timeout: float) -> Runtime:
        """Run the target with command line arguments."""

        return run(*self.args, *args, timeout=timeout)
