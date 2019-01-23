from typing import Callable

from .runtime import Target, Runtime
from .message import Messenger


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

    def __repr__(self):
        return str(self)


Testable = Callable[[Target, Messenger], Result]


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

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self)

    def run(self, target: Target, message: Messenger) -> Result:
        """Run the test with context and target."""

        return self._test(target, message)
