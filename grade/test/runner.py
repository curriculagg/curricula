from typing import Dict, List, Optional

from .runtime import Target
from .test import Test, Result
from .message import Messenger


class Runner:
    """A linear test runner."""

    results: Dict[Test, Optional[Result]]

    def __init__(self):
        self.results = {}

    def load(self, tests: List[Test]):
        """Load all test cases into the system."""

        for test in tests:
            self.results[test] = None

    def run(self, target: Target):
        """Run all tests on a target."""

        message = Messenger()
        for test in self.results:
            result = test.run(target, message)
            print(test, result)
            message.print(prefix=" " * 2)
