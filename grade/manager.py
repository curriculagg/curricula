from typing import Dict, List, Callable

from grade.test import Result, Test, Runnable
from grade.correctness import CorrectnessTest
from grade.resource import Executable
from grade.library.message import Messenger
from grade.library.utility import name_from_doc, timed


def create_registrar(self: "Manager", test: type, **details):
    """A second-level decorator to reuse code."""

    def decorator(runnable: Runnable) -> Runnable:
        """Put the function in a correctness object."""

        name = details.pop("name", name_from_doc(runnable))
        assert name is not None, "test name must be provided in registration or docstring"
        self.tests.append(test(name, runnable, **details))
        return runnable

    return decorator


# Correctness requires an executable
# Complexity requires an executable
# Style requires a file path


class Manager:
    """An overarching manager for test registrars."""

    tests: List[Test]

    def __init__(self):
        self.tests = []

    def correctness(self, **details) -> Callable:
        """Register a new correctness test with the container."""

        return create_registrar(self, CorrectnessTest, **details)

    # TODO: targets will be assigned via names, need a way to decide if make executable or just raw file, etc.

    @timed(name="Tests")
    def run(self, target: Executable) -> Dict[Test, Result]:
        """Run all tests on a target."""

        print("Starting tests...")
        results = {}
        message = Messenger()
        for test in self.tests:
            result = test.run(target, message)
            message.sneak("{} {}".format(test, result))
            print(message.build(prefix=" " * 2))

        return results

