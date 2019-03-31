import inspect
from typing import List, Dict

from grade.test import Result, Test
from grade.resource import Logger, Resource
from grade.library.utility import timed


class Runner:
    """A linear test runner."""

    tests: Dict[Test, Result]

    def __init__(self):
        self.tests = dict()

    def load(self, tests: List[Test]):
        """Load all test cases into the system."""

        self.tests = {test: None for test in tests}

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

            result = test.run(**dependencies)

            log.sneak("{} {}".format(test, result))
            print(log.build(prefix="  "))

        return self.tests
