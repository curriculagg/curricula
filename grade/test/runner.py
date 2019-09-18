import inspect
from typing import Optional, Callable, Dict

from . import Result, Test, Runnable
from .correctness import CorrectnessTest
from .complexity import ComplexityTest
from ..resource import Logger, Resource
from ..library.utility import timed, name_from_doc


def create_registrar(self: "Runner", test: type, **details):
    """A second-level decorator to reuse code."""

    def decorator(runnable: Runnable) -> Runnable:
        """Put the function in a correctness object."""

        name = details.pop("name", name_from_doc(runnable))
        assert name is not None, "test name must be provided in registration or docstring"
        self.tests[test(name, runnable, **details)] = None
        return runnable

    return decorator


class Runner:
    """A linear test runner."""

    tests: Dict[Test, Optional[Result]]

    def __init__(self):
        self.tests = dict()

    def correctness(self, **details) -> Callable:
        """Register a new correctness test with the container."""

        return create_registrar(self, CorrectnessTest, **details)

    def complexity(self, **details) -> Callable:
        """Register a new correctness test with the container."""

        return create_registrar(self, ComplexityTest, **details)

    @timed(name="Tests")
    def run(self, **resources: Resource) -> Dict[Test, Result]:
        """Run all tests on a target."""

        print("Starting tests...")
        for test in self.tests:
            log = Logger()

            dependencies = {}
            for name, parameter in inspect.signature(test.runnable).parameters.items():

                # Provide a logger for all typed arguments
                if parameter.annotation == Logger:
                    dependencies[name] = log
                    continue

                # Otherwise, fill resource first from override then from default
                dependency = resources.get(name, parameter.default)
                assert dependency != parameter.empty, "could not satisfy dependency {} in {}".format(name, test.name)

            self.tests[test] = result = test.run(**dependencies)

            log.sneak("{} {}".format(test, result))
            print(log.build(prefix="  "))

        return self.tests
