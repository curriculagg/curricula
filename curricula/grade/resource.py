from typing import Dict, Tuple
from pathlib import Path
from dataclasses import dataclass, field

from .library import callgrind, process

__all__ = ("Resource", "Context", "File", "Executable", "ExecutableFile")


class Resource:
    """A resource required for a test."""


@dataclass(eq=False)
class Context(Resource):
    """The execution context of the tests."""

    target_path: Path
    options: Dict[str, str] = field(default_factory=dict)


@dataclass(eq=False)
class File(Resource):
    """A resource corresponding to a file."""

    path: Path


@dataclass(eq=False)
class Executable(Resource):
    """A runnable testing target program."""

    args: Tuple[str, ...]

    def __init__(self, *args: str):
        self.args = args

    def execute(self, *args: str, timeout: float) -> process.Runtime:
        """Run the target with command line arguments."""

        return process.run(*self.args, *args, timeout=timeout)

    def count(self, *args: str, timeout: float) -> int:
        """Count the instructions executed during runtime."""

        return callgrind.run(*self.args, *args, timeout=timeout)


@dataclass(eq=False)
class ExecutableFile(Executable, File):
    """A local file that can be executed."""

    def __init__(self, path: Path, *args: str):
        super().__init__()
        self.path = path
        self.args = (str(path),) + args

    def execute(self, *args: str, timeout: float) -> process.Runtime:
        """Run the target with command line arguments."""

        return process.run(*self.args, *args, timeout=timeout)

    def count(self, *args: str, timeout: float) -> int:
        """Count the instructions executed during runtime."""

        return callgrind.run(*self.args, *args, timeout=timeout)
