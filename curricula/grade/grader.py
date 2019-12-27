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


def fulfills_dependencies(task: Task, report: Report):
    """Convenience."""

    return all(report.check(dependency) for dependency in task.dependencies)


def sanity_enabled_and_not_sanity(task: Task, resources: dict):
    """Convenience."""

    context = resources["context"]
    if "sanity" not in context.options or not context.options["sanity"]:
        return False
    if "sanity" in task.details and task.details["sanity"]:
        return False
    return True


def run_tasks(tasks: List[Task], report: Report, resources: dict):
    """Execute sorted tasks, skipping if missing dependencies."""

    log.debug("running tasks")
    for task in tasks:
        log.debug(f"running task {task.name}")

        # Check conditions for whether this case is visible
        hidden = sanity_enabled_and_not_sanity(task, resources)

        # Run task if not hidden and dependencies are met
        if not hidden and fulfills_dependencies(task, report):
            result = task.run(resources)
        else:
            result = task.result_type.incomplete()

        # Set the origin task and add to report
        result.task = task
        report.add(result, hidden=hidden)


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
