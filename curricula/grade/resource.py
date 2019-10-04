import sys
from collections import deque
from typing import Deque, Dict, Tuple
from pathlib import Path
from dataclasses import dataclass, field

from .library import callgrind, process

__all__ = ("Resource", "Context", "Logger", "File", "Executable")


class Resource:
    """A resource required for a test."""


@dataclass
class Context(Resource):
    """The execution context of the tests."""

    target_path: Path
    options: Dict[str, str] = field(default_factory=dict)


@dataclass
class Logger(Resource):
    """A mutable message recipient.

    This is used in tests so that when multiprocessing output is
    buffered and therefore kept  separate for independent test cases.
    """

    messages: Deque[str] = field(default_factory=deque)
    indent: int = 0

    def __call__(self, *message, sep: str = " ", end: str = "\n"):
        """Place a message on the queue."""

        self.messages.append(" " * self.indent + sep.join(map(str, message)) + end)
        self.indent = 0

    def __getitem__(self, count: int) -> "Logger":
        """Set indent."""

        self.indent = count
        return self

    def sneak(self, *message, sep: str = " ", end: str = "\n"):
        """Sneak in a message at the head."""

        self.messages.appendleft(" " * self.indent + sep.join(map(str, message)) + end)

    def print(self, prefix="", file=sys.stdout):
        """Build the complete output as a string."""

        if not self.messages:
            return

        out = "".join(message for message in self.messages)
        self.messages.clear()
        print("\n".join(prefix + line for line in out.split("\n")).rstrip(), file=file)

    def clear(self):
        self.messages.clear()


@dataclass
class File(Resource):
    """A resource corresponding to a file."""

    path: str


@dataclass
class Executable(Resource):
    """A runnable testing target program."""

    args: Tuple[str]

    def __init__(self, *args: str):
        self.args = args

    def execute(self, *args: str, timeout: float) -> process.Runtime:
        """Run the target with command line arguments."""

        return process.run(*self.args, *args, timeout=timeout)

    def count(self, *args: str, timeout: float) -> int:
        """Count the instructions executed during runtime."""

        return callgrind.run(*self.args, *args, timeout=timeout)
