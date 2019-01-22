"""A lightweight unit test framework."""

import timeit
from typing import Callable, List, Iterator, Dict

from .runtime import Target, Runtime


class Result:
    """The result of a test case."""

    runtime: Runtime
    passing: bool

    def __init__(self, runtime: Runtime, passing: bool):
        self.runtime = runtime
        self.passing = passing


Testable = Callable[[Target], Iterator[Result, None]]


class Test:
    """A wrapper for a single test case."""

    run: Testable
    name: str

    def __init__(self, run: Testable, **details):
        """Initialize the test and look for registration details."""

        self.run = run
        assert "name" in details, "test must be registered with name"
        self.name = details["name"]


class Tests:
    """A test case container."""

    name: str

    tests: Dict[str, List[Test]] = {}
    current: List[Test] = None

    def __init__(self, name: str):
        self.name = name

    def file(self, file: str):
        """Indicate that tests for a new file are being registered."""

        new = []
        self.tests[file] = new
        self.current = new

    def register(self, **details) -> Callable[[Testable], Testable]:
        """Register a new test with the container."""

        assert self.current is not None, "tests are not registered to a file"

        def decorator(run: Testable) -> Testable:
            self.current.append(Test(run, **details))
            return run

        return decorator

    def run(self, target: Target):
        """Run all the tests registered with the container."""

        for path in self.tests:
            for test in self.tests[path]:
                generator = test.run(target)
                result = next(generator)
                next(generator, None)


tests: Tests = Tests("all tests")
