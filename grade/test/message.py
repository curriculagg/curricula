from typing import Deque

from collections import deque


class Messenger:
    """A mutable message recipient."""

    __slots__ = ("messages",)

    messages: Deque[str]

    def __init__(self):
        self.messages = deque()

    def __call__(self, *message, sep: str = " ", end: str = "\n"):
        """Place a message on the queue."""

        self.messages.append(sep.join(map(str, message)) + end)

    def sneak(self, *message, sep: str = " ", end: str = "\n"):
        """Sneak in a message at the head."""

        self.messages.appendleft(sep.join(map(str, message)) + end)

    def build(self, prefix="") -> str:
        """Build the complete output as a string."""

        out = "".join(message for message in self.messages)
        self.messages.clear()
        return "\n".join(prefix + line for line in out.split("\n")).rstrip()
