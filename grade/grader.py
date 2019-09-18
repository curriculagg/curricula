from typing import List
from dataclasses import dataclass, field

from .test import Runnable, Test
from .build import Build
from .library.utility import name_from_doc


def create_registrar(container: List, wrapper: type, **details):
    """A second-level decorator to reuse code."""

    def decorator(runnable: Runnable) -> Runnable:
        """Put the function in a correctness object."""

        name = details.pop("name", name_from_doc(runnable))
        assert name is not None, "name must be provided in registration or docstring"
        container.append(wrapper(name, runnable, **details))
        return runnable

    return decorator


@dataclass
class Grader:
    """A main class for grading runtime."""

    tests: List[Test] = field(default_factory=list)
    builds: List[Build] = field(default_factory=list)

    def test(self, **details):
        """Add a test to the grader."""

        return create_registrar(self.tests, Test, **details)

    def build(self, **details):
        """Add a test to the grader."""

        return create_registrar(self.builds, Build, **details)
