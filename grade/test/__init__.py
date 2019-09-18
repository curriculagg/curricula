from typing import Callable
from dataclasses import dataclass

from ..resource import *


@dataclass
class Result:
    """The result of a test."""

    details: dict

    def __init__(self, **details):
        self.details = details

    def __repr__(self):
        return "Result({})".format(str(self))


Runnable = Callable[..., Result]


@dataclass
class Test:
    """A general test for a codebase.

    From this class the correctness, complexity, and style tests are
    derived such that they can be run generically. It is intended to
    wrap a raw runnable with metadata used during registration.
    """

    name: str
    runnable: Runnable
    details: dict

    def __str__(self):
        return self.name

    def __hash__(self):
        return id(self)

    def run(self, **resources: Resource) -> Result:
        """Do the dependency injection for the runnable."""

        return self.runnable(**resources)
