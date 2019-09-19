from typing import Optional, List, Dict

from . import Result, Test
from ..report import Report
from ..resource import Logger, Resource


class Runner:
    """A linear test runner."""

    tests: Dict[Test, Optional[Result]]

    def __init__(self, tests: List[Test]):
        self.tests = {test: None for test in tests}

    def run(self, report: Report, resources: Dict[str, Resource]) -> Dict[Test, Result]:
        """Run all tests on a target."""

        for test in self.tests:
            log = Logger()
            resources.update(log=log)

            self.tests[test] = result = test.run(resources)
            report.add(result)

            log.sneak("{} {}".format(test, result))
            log.write(prefix="  ")

        return self.tests
