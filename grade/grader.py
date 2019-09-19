from typing import List, Callable
from dataclasses import dataclass, field

from .report import Report
from .resource import Logger
from .check import Check
from .build import Build
from .task import Task, Runnable
from .test import Test
from .test.runner import Runner
from .library.utility import timed


def create_registrar(details: dict, factory: Callable[..., Task], container: List):
    """A second-level decorator to reuse code."""

    def decorator(runnable: Runnable) -> Runnable:
        """Put the function in a correctness object."""

        container.append(factory(
            name=runnable.__qualname__,
            description=runnable.__doc__,
            details=details,
            runnable=runnable))
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

        return create_registrar(details, Check, self.checks)

    def test(self, **details):
        """Add a test to the grader."""

        return create_registrar(details, Test, self.tests)

    def build(self, **details):
        """Add a test to the grader."""

        return create_registrar(details, Build, self.builds)

    def _do_check(self, resources: dict):
        """Checks stage."""

        print("Starting checks...")
        report = resources["report"]
        report.stage = "check"
        for check in self.checks:
            result = check.run(resources)
            report.add(result)
            if not result.okay and check.required:
                raise GraderException("failed required check")
            resources["log"].print()

    def _do_build(self, resources: dict):
        """Build stage."""

        print("Starting build...")
        report = resources["report"]
        report.stage = "build"
        for build in self.builds:
            result = build.run(resources)
            report.add(result)
            if not result.okay and build.required:
                raise GraderException("failed required build")
            if result.inject:
                resources[result.inject] = result.executable
            resources["log"].print()

    def _do_test(self, resources: dict):
        """Test stage."""

        report = resources["report"]
        if resources["context"].options.get("sanity"):
            return

        print("Starting tests...")
        report.stage = "test"
        runner = Runner(self.tests)
        runner.run(resources)

    @timed(name="Grader")
    def run(self, **resources) -> Report:
        """Build and test."""

        report = Report()
        resources.update(report=report, log=Logger())

        for stage in (self._do_check, self._do_build, self._do_test):
            try:
                stage(resources)
            except GraderException:
                break

        return report
