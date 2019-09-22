from typing import Optional, List, Dict

from ..task import Task, Result


class Runner:
    """A linear test runner."""

    tests: Dict[Task, Optional[Result]]

    def __init__(self, tests: List[Task]):
        self.tests = {test: None for test in tests}

    def run(self, resources: dict) -> Dict[Task, Result]:
        """Run all tests on a target."""

        for test in self.tests:
            self.tests[test] = result = test.run(resources)
            resources["report"].add(result)
            resources["log"].sneak("{} {}".format(test, result))
            resources["log"].print(prefix="  ")

        return self.tests
