from typing import List
from dataclasses import dataclass, field

from .report import Report
from .resource import Logger
from .task import Task, Runnable, Incomplete
from curricula.library.utility import timed


def create_registrar(kind: str, details: dict, container: List):
    """A second-level decorator to reuse code."""

    def decorator(runnable: Runnable) -> Runnable:
        """Put the function in a correctness object."""

        container.append(Task(
            name=details.pop("name", runnable.__qualname__),
            description=details.pop("description", runnable.__doc__),
            kind=kind,
            required=details.pop("required", False),
            runnable=runnable,
            details=details,))
        return runnable

    return decorator


class GraderException(Exception):
    """Thrown during checks, builds, tests."""


@dataclass
class Grader:
    """A main class for grading runtime."""

    failed: bool = False
    setups: List[Task] = field(default_factory=list)
    tests: List[Task] = field(default_factory=list)
    teardowns: List[Task] = field(default_factory=list)

    def setup(self, **details):
        """Add a setup to the grader."""

        return create_registrar("setup", details, self.setups)

    def test(self, **details):
        """Add a test to the grader."""

        return create_registrar("test", details, self.tests)

    def teardown(self, **details):
        """Add a teardown to the grader."""

        return create_registrar("teardown", details, self.teardowns)

    def _run(self, tasks: List[Task], resources: dict):
        """Checks stage."""

        report = resources["report"]
        report.stage = "setup"
        for task in tasks:
            result = Incomplete(task) if self.failed else task.run(resources)
            report.add(result)
            if not self.failed:
                resources["log"].sneak("{} {}".format(task, result))
                resources["log"].print(prefix=" " * 2)
            if task.required and (not result.complete or not result.passed):
                self.failed = True

    @timed(name="Grader")
    def run(self, **resources) -> Report:
        """Build and test."""

        report = Report()
        resources.update(report=report, log=Logger(), resources=resources)

        for name, tasks in (("setup", self.setups), ("tests", self.tests), ("teardown", self.teardowns)):
            if len(tasks) == 0:
                continue
            print(f"Starting {name}")
            self._run(tasks, resources)

        return report
