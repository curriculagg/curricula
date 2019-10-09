import itertools
from typing import List, Dict
from dataclasses import dataclass, field

from .report import Report
from .resource import Logger
from .task import Task, Runnable, Incomplete
from ..library.utility import timed


def create_registrar(kind: str, details: dict, container: List):
    """A second-level decorator to reuse code."""

    def decorator(runnable: Runnable) -> Runnable:
        """Put the function in a correctness object."""

        name = details.pop("name", runnable.__qualname__)
        description = details.pop("description", runnable.__doc__)
        dependencies = details.pop("dependencies", ())
        if isinstance(dependencies, str):
            dependencies = (dependencies,)

        container.append(Task(
            name=name,
            description=description,
            kind=kind,
            dependencies=dependencies,
            runnable=runnable,
            details=details))
        return runnable

    return decorator


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


def run_tasks(tasks: List[Task], report: Report, resources: dict = None, ignore_result: bool = False):
    """Execute sorted tasks, skipping if missing dependencies."""

    for task in tasks:
        satisfied = all(report.check(dependency) for dependency in task.dependencies)
        result = Incomplete(task) if not satisfied else task.run(resources or dict())
        if ignore_result:
            continue

        report.add(result)
        if satisfied:
            resources["log"].sneak("{} {}".format(task, result))
            resources["log"].print(prefix=" " * 2)


@dataclass
class Grader:
    """A main class for grading runtime."""

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

    def check(self):
        """Topologically sort tasks, checking for cycles."""

        topological_sort(self.setups, self.tests, self.teardowns)

    @timed(name="Grader")
    def run(self, **resources) -> Report:
        """Build and test."""

        report = Report()
        resources.update(report=report, log=Logger(), resources=resources)

        for name, tasks in (("setup", self.setups), ("tests", self.tests), ("teardown", self.teardowns)):
            if len(tasks) == 0:
                continue
            print(f"Starting {name}")
            run_tasks(tasks, report, resources, ignore_result=name == "teardown")

        return report

    def dump(self) -> list:
        """Dump the tasks to something JSON serializable."""

        return [task.dump() for task in itertools.chain(self.setups, self.tests, self.teardowns)]
