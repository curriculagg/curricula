from typing import List

from .test import Test, Testable
from .reflection import name_from_doc


class Manager:
    """A test case container."""

    tests: List[Test]

    def __init__(self):
        self.tests = []

    def register(self, **details):
        """Register a new test with the container."""

        def decorator(test: Testable) -> Testable:
            """Put the function in a test object."""

            name = details.pop("name", name_from_doc(test))
            assert name is not None, "name must be provided in registration or docstring"
            self.tests.append(Test(test, name, **details))
            return test

        return decorator
