from collections import deque
from typing import Deque, Optional, Tuple

from .library import callgrind
from .library import process


class Resource:
    """A resource required for a test."""


class Logger(Resource):
    """A mutable message recipient.

    This is used in tests so that when multiprocessing output is
    buffered and therefore kept  separate for independent test cases.
    """

    messages: Deque[str]
    indent: int = 0

    def __init__(self):
        self.messages = deque()

    def __repr__(self):
        return "Logger()".format()

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
        self.indent = 0

    def build(self, prefix="") -> str:
        """Build the complete output as a string."""

        out = "".join(message for message in self.messages)
        self.messages.clear()
        return "\n".join(prefix + line for line in out.split("\n")).rstrip()


class File(Resource):
    """A resource corresponding to a file."""

    path: str

    def __init__(self, path: Optional[str]):
        """Require a path to exist."""

        self.path = path

    def __repr__(self):
        return "File({})".format(self.path)


class Executable(Resource):
    """A runnable testing target program."""

    args: Tuple[str]

    def __init__(self, *args: str):
        """Initialize a target with commands to run the target.

        Any paths invoked in the executable command must be absolute; relative
        requires subprocess configuration that is unsafe.
        """

        self.args = tuple(args)

    def execute(self, *args: str, timeout: float) -> process.Runtime:
        """Run the target with command line arguments."""

        return process.run(*self.args, *args, timeout=timeout)

    def count(self, *args: str, timeout: float) -> int:
        """Count the instructions executed during runtime."""

        return callgrind.run(*self.args, *args, timeout=timeout)

    def __repr__(self):
        return "Executable({})".format(" ".join(self.args))
