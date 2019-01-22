"""A lightweight unit test framework."""

from typing import Callable, Optional, Dict

from .runtime import Target, Runtime


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

    def __init__(self, run: Testable, **details):
        """Initialize the test and look for registration details."""

        self.run = run
        self.name = details["name"]


class Tests:
    """A test case container."""

    tests: Dict[Test, Optional[Result]] = {}

    def register(self, **details):
        """Register a new test with the container."""

        assert "name" in details, "test must be registered with name"

        def decorator(run: Testable):
            """Put the function in a test object.

            We don't return the test function here because it should
            not be used outside of the tests manager.
            """

            def decorated(target: Target) -> Result:
                """The actual test to be run."""

                print("Running {}".format(details["name"]))
                result = run(target)
                print(result, "***" if not result.passing else "")
                return result

            self.tests[Test(decorated, **details)] = None

        return decorator

    def run(self, target: Target):
        """Run all the tests registered with the container."""

        for test in self.tests:
            self.tests[test] = test.run(target)
