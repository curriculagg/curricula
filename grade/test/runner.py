import inspect
from typing import Optional, List, Dict

from . import Result, Test
from ..resource import Logger, Resource
from ..library.utility import timed


class Runner:
    """A linear test runner."""

    tests: Dict[Test, Optional[Result]]

    def __init__(self, tests: List[Test]):
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
                dependencies[name] = dependency

            self.tests[test] = result = test.run(**dependencies)

            log.sneak("{} {}".format(test, result))
            print(log.build(prefix="  "))

        return self.tests
