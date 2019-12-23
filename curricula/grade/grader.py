import itertools
from typing import List, Dict
from dataclasses import dataclass, field

from .report import Report
from .resource import Logger
from .task import Task
from ..library.utility import timed

from .setup import SetupStage
from .test import TestStage
from .teardown import TeardownStage


class GraderException(Exception):
    """Thrown during checks, builds, tests."""


def topological_sort_visit(task: Task, lookup: Dict[str, Task], marks: Dict[Task, int], result: List[Task]):
    """Visit a node."""

    if marks[task] == 2:
        return
    if marks[task] == 1:
        raise ValueError("Found cycle!")
    marks[task] = 1
    for dependency in task.dependencies:
        topological_sort_visit(lookup[dependency], lookup, marks, result)
    marks[task] = 2
    result.append(task)


def topological_sort(*steps: List[Task]):
    """Order tasks by dependency."""

    lookup = {}
    marks = {}
    for tasks in steps:
        result = []
        for task in tasks:
            marks[task] = 0
            lookup[task.name] = task
        for task in tasks:
            if marks[task] != 2:
                topological_sort_visit(task, lookup, marks, result)
        tasks.clear()
        tasks.extend(result)


def run_tasks(tasks: List[Task], report: Report, resources: dict = None):
    """Execute sorted tasks, skipping if missing dependencies."""

    resources = resources or dict()
    for task in tasks:
        satisfied = all(report.check(dependency) for dependency in task.dependencies)
        result = task.result_type.incomplete() if not satisfied else task.run(resources)
        report.add(result)
        if satisfied:
            symbol = "\u2713" if result.passed else "\u2717"
            resources["log"].sneak(f"{symbol} {task} {result}")
            resources["log"].print(prefix=" " * 2)


@dataclass(eq=False)
class Grader:
    """A main class for grading runtime."""

    setup: SetupStage = field(default_factory=SetupStage)
    test: TestStage = field(default_factory=TestStage)
    teardown: TeardownStage = field(default_factory=TeardownStage)

    def check(self):
        """Topologically sort tasks, checking for cycles."""

        topological_sort(self.setup.tasks, self.test.tasks, self.teardown.tasks)

    @timed(name="Grader")
    def run(self, **resources) -> Report:
        """Build and test."""

        report = Report()
        resources.update(report=report, log=Logger(), resources=resources)
        zipped = (("setup", self.setup.tasks), ("test", self.test.tasks), ("teardown", self.teardown.tasks))

        for name, tasks in zipped:
            if len(tasks) == 0:
                continue
            print(f"Starting {name}")
            run_tasks(tasks, report, resources)

        return report

    def dump(self) -> dict:
        """Dump the tasks to something JSON serializable."""

        return {task.name: task.dump() for task in
                itertools.chain(self.setup.tasks, self.test.tasks, self.teardown.tasks)}
