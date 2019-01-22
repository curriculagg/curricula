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
        return "{} in {} seconds".format(
            "passed" if self.passing else "failed",
            round(self.runtime.elapsed, 2))


Testable = Callable[[Target], Result]


class Test:
    """A wrapper for a single test case."""

    run: Testable
    name: str

    def __init__(self, test: Testable, name: str, **details):
        """Initialize the test and look for registration details."""

        self.run = test
        self.name = name


class Tests:
    """A test case container."""

    tests: Dict[Test, Optional[Result]] = {}

    def register(self, middleware: Callable[[Callable], Testable] = None, **details):
        """Register a new test with the container.

        To be quite honest, the reason we're using middleware instead
        of another decorator is because it is rather aesthetically
        unappealing.
        """

        def decorator(test: Callable):
            """Put the function in a test object."""

            # Name will always be in details
            details["name"] = details.get("name", name_from_doc(test))

            # Apply middleware
            if middleware is not None:
                test = middleware(test, **details)

            self.tests[Test(test, **details)] = None

        return decorator

    def run(self, target: Target):
        """Run all the tests registered with the container."""

        for test in self.tests:
            self.tests[test] = test.run(target)
