from collections import deque
from typing import Deque


class Messenger:
    """A mutable message recipient.

    This is used in tests so that when multiprocessing output is
    buffered and therefore kept  separate for independent test cases.
    """

    messages: Deque[str]
    indent: int = 0

    def __init__(self):
        self.messages = deque()

    def __call__(self, *message, sep: str = " ", end: str = "\n"):
        """Place a message on the queue."""

        self.messages.append(" " * self.indent + sep.join(map(str, message)) + end)
        self.indent = 0

    def __getitem__(self, count: int) -> "Messenger":
        """Set tabulation."""

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
