"""A lightweight unit test framework."""

from ctypes import CDLL
from typing import Callable, List, Tuple, Dict
import timeit

from .printer import Printer


class Result:
    """A result returned from a test case."""

    passed: bool
    reason: Tuple[str]

    def __init__(self, passed: bool, *reason: str):
        self.passed = passed
        self.reason = tuple(filter(None, reason))


TestCallable = Callable[[CDLL], Result]


class Test:
    """A wrapper for a single test case."""

    run: TestCallable
    name: str

    def __init__(self, run: TestCallable, **details):
        self.run = run

        assert "name" in details, "test must be registered with name"
        self.name = details["name"]


class Tests:
    """A test case container."""

    name: str

    tests: Dict[str, List[Test]] = {}
    current: List[Test] = None
    print: Printer = Printer()

    def __init__(self, name: str):
        self.name = name

    def file(self, file: str):
        """Indicate that tests for a new file are being registered."""

        new = []
        self.tests[file] = new
        self.current = new

    def register(self, **details) -> Callable[[TestCallable], TestCallable]:
        """Register a new test with the container."""

        assert self.current is not None, "tests are not registered to a file"

        def decorator(run: TestCallable):
            self.current.append(Test(run, **details))
            return run

        return decorator

    def run(self, library: CDLL):
        """Run all the tests registered with the container."""

        for path in self.tests:

            self.print("running {}".format(path))
            self.print.indent()

            for test in self.tests[path]:
                start = timeit.default_timer()
                result = test.run(library)
                elapsed = timeit.default_timer() - start
                self.print(test.name, end=False)
                self.format(result, elapsed)

            self.print.dedent()
        self.print.dedent()

    def format(self, result: Result, total: float):
        """Format and print a result."""

        line = " passed" if result.passed else " failed"
        line += " in " + str(round(total, 2)) + " seconds"

        # Add stars if failed
        if not result.passed:
            line += " ***"

        self.print(line)

        # Print reasons
        if len(result.reason) > 0:
            self.print.indent()
            for line in result.reason:
                self.print(line or "(no output)")
            self.print.dedent()


tests: Tests = Tests("all tests")
