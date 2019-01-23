"""A lightweight unit test framework."""

from typing import Callable, Optional, Dict

from .runtime import Target, Runtime
from .utility import name_from_doc


class Result:
    """The result of a test case."""

    runtime: Runtime
    passing: bool

    def __init__(self, runtime: Runtime, passing: bool):
        self.runtime = runtime
        self.passing = passing

    def __str__(self):
        if self.runtime.timeout is not None:
            return "timed out in {} seconds".format(self.runtime.timeout)
        return "{} in {} seconds".format(
            "passed" if self.passing else "failed",
            round(self.runtime.elapsed, 5))


Testable = Callable[["Test", Target], Result]


class Test:
    """A wrapper for a single test case."""

    _test: Testable
    name: str
    details: dict

    def __init__(self, test: Testable, name: str, **details):
        """Initialize the test and look for registration details."""

        self._test = test
        self.name = name
        self.details = details

    def run(self, target: Target) -> Result:
        """Run the test with context and target."""

        return self._test(self, target)


class Tests:
    """A test case container."""

    tests: Dict[Test, Optional[Result]] = {}

    def register(self, **details):
        """Register a new test with the container.

        To be quite honest, the reason we're using middleware instead
        of another decorator is because it is rather aesthetically
        unappealing.
        """

        def decorator(test: Testable) -> Testable:
            """Put the function in a test object."""

            name = details.pop("name", name_from_doc(test))
            assert name is not None, "name must be provided in registration or docstring"

            self.tests[Test(test, name, **details)] = None
            return test

        return decorator

    def run(self, target: Target):
        """Run all the tests registered with the container."""

        for test in self.tests:
            self.tests[test] = test.run(target)
