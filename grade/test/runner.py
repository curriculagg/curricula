from typing import Dict, List

from .runtime import Target
from .test import Test, Result
from .message import Messenger
from .utility import timed


class Runner:
    """A linear test runner."""

    tests: List[Test]

    def __init__(self):
        self.tests = []

    def load(self, tests: List[Test]):
        """Load all test cases into the system."""

        self.tests = tests.copy()

    @timed(name="Tests")
    def run(self, target: Target) -> Dict[Test, Result]:
        """Run all tests on a target."""

        print("Starting tests...")
        results = {}
        message = Messenger()
        for test in self.tests:
            result = test.run(target, message)
            message.sneak("{} {}".format(test, result))
            print(message.build())

        return results
