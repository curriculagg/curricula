from typing import Deque

from collections import deque


class Messenger:
    """A mutable message recipient."""

    __slots__ = ("messages",)

    messages: Deque[str]

    def __init__(self):
        self.messages = deque()

    def __call__(self, *message, sep=" "):
        """Place a message on the queue."""

        self.messages.append(sep.join(map(str, message)))

    def sneak(self, message: str):
        """Sneak in a message at the head."""

        self.messages.appendleft(message)

    def build(self, prefix="") -> str:
        """Build the complete output as a string."""

        out = "\n".join(prefix + message for message in self.messages)
        self.messages.clear()
        return out
