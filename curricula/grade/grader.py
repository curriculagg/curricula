import itertools
from typing import List, Dict
from dataclasses import dataclass, field

from .report import Report
from .task import Task
from ..library.log import log

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
        log.error("found cycle in task dependencies")
        raise ValueError()

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

    log.debug("running tasks")
    resources = resources or dict()
    for task in tasks:
        log.debug(f"running task {task.name}")
        if all(report.check(dependency) for dependency in task.dependencies):
            result = task.run(resources)
        else:
            result = task.result_type.incomplete()
        result.task = task
        report.add(result)


@dataclass(eq=False)
class Grader:
    """A main class for grading runtime."""

    setup: SetupStage = field(default_factory=SetupStage)
    test: TestStage = field(default_factory=TestStage)
    teardown: TeardownStage = field(default_factory=TeardownStage)

    def check(self):
        """Topologically sort tasks, checking for cycles."""

        log.debug("sorting grader tasks by dependency")
        topological_sort(self.setup.tasks, self.test.tasks, self.teardown.tasks)

    def run(self, **resources) -> Report:
        """Build and test."""

        log.debug("setting up runtime")
        report = Report()
        resources.update(report=report, resources=resources)

        for stage in (self.setup, self.test, self.teardown):
            if len(stage.tasks) == 0:
                log.debug(f"skipping stage {stage.name}")
                continue
            log.debug(f"starting stage {stage.name}")
            run_tasks(stage.tasks, report, resources)

        return report

    def dump(self) -> dict:
        """Dump the tasks to something JSON serializable."""

        return {task.name: task.dump() for task in
                itertools.chain(self.setup.tasks, self.test.tasks, self.teardown.tasks)}
