from typing import List, Callable
from dataclasses import dataclass, field

from .report import Report
from .check import Check
from .build import Build
from .resource import inject
from .task import Task, Runnable
from .test import Test
from .test.runner import Runner
from .library.utility import name_from_doc


def create_registrar(container: List, factory: Callable[[str, Runnable, dict], Task], details: dict):
    """A second-level decorator to reuse code."""

    def decorator(runnable: Runnable) -> Runnable:
        """Put the function in a correctness object."""

        name = details.pop("name", name_from_doc(runnable))
        assert name is not None, "name must be provided in registration or docstring"
        container.append(factory(name, runnable, details))
        return runnable

    return decorator


class GraderException(Exception):
    """Thrown during checks, builds, tests."""


@dataclass
class Grader:
    """A main class for grading runtime."""

    checks: List[Check] = field(default_factory=list)
    tests: List[Test] = field(default_factory=list)
    builds: List[Build] = field(default_factory=list)

    def check(self, **details):
        """Add a check to the grader."""

        return create_registrar(self.checks, Check, details)

    def test(self, **details):
        """Add a test to the grader."""

        return create_registrar(self.tests, Test, details)

    def build(self, **details):
        """Add a test to the grader."""

        return create_registrar(self.builds, Build, details)

    def _do_check(self, report: Report, resources: dict):
        """Checks stage."""

        print("Starting checks...")
        report.stage = "check"
        for check in self.checks:
            check.run(inject(check.runnable, resources))

    def _do_build(self, report: Report, resources: dict):
        """Build stage."""

        print("Starting build...")
        report.stage = "build"
        for build in self.builds:
            resources[build.name] = build.run(inject(build.runnable, resources))

    def _do_test(self, report: Report, resources: dict):
        """Test stage."""

        if resources["context"].options.get("sanity"):
            return

        print("Starting tests...")
        report.stage = "test"
        runner = Runner(self.tests)
        runner.run(resources)

    def run(self, **resources) -> Report:
        """Build and test."""

        report = Report()
        resources.update(report=report)

        for stage in (self._do_check, self._do_build, self._do_test):
            try:
                stage(report, resources)
            except GraderException:
                break

        return report
