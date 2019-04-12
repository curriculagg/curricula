from typing import List, Callable

from grade.test import Test, Runnable
from grade.correctness import CorrectnessTest
from grade.library.utility import name_from_doc


def create_registrar(self: "Manager", test: type, **details):
    """A second-level decorator to reuse code."""

    def decorator(runnable: Runnable) -> Runnable:
        """Put the function in a correctness object."""

        name = details.pop("name", name_from_doc(runnable))
        assert name is not None, "test name must be provided in registration or docstring"
        self.tests.append(test(name, runnable, **details))
        return runnable

    return decorator


class Manager:
    """An overarching manager for test registrars."""

    tests: List[Test]

    def __init__(self):
        self.tests = []

    def correctness(self, **details) -> Callable:
        """Register a new correctness test with the container."""

        return create_registrar(self, CorrectnessTest, **details)
