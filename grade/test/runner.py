from typing import Optional, List, Dict

from . import Result, Test


class Runner:
    """A linear test runner."""

    tests: Dict[Test, Optional[Result]]

    def __init__(self, tests: List[Test]):
        self.tests = {test: None for test in tests}

    def run(self, resources: dict) -> Dict[Test, Result]:
        """Run all tests on a target."""

        for test in self.tests:
            self.tests[test] = result = test.run(resources)
            resources["report"].add(result)
            resources["log"].sneak("{} {}".format(test, result))
            resources["log"].print(prefix="  ")

        return self.tests
