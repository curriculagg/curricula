from typing import Deque

from collections import deque


class Messenger:
    """A mutable message recipient."""

    messages: Deque[str]

    def __init__(self):
        self.messages = deque()

    def __call__(self, message: str):
        """Place a message on the queue."""

        self.messages.append(message)

    def print(self, prefix=""):
        """Print and clear all messages."""

        for message in self.messages:
            print(prefix + message)
        self.messages.clear()
