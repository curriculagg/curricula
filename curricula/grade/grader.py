from typing import List, Tuple, Iterator, Set, Optional, Callable, Dict, Iterable
from dataclasses import dataclass, field

from .report import ProblemReport
from .task import Task, Result
from .stage import GraderStage
from .exception import GraderException
from ..log import log

from .resource import Context, Submission
from .dependency import topological_sort
from .setup import SetupStage
from .test import TestStage
from .teardown import TeardownStage

import typing

if typing.TYPE_CHECKING:
    from .models import GradingProblem


def fulfills_dependencies(task: Task, report: ProblemReport):
    """Convenience."""

    return all((
        all(report[dependency].passing for dependency in task.dependencies.passing),
        all(report[dependency].complete for dependency in task.dependencies.complete)))


def flatten_dependencies(task_name: str, task_lookup: Dict[str, Task]) -> Iterator[str]:
    """Return a flattened iterable of dependencies task names."""

    for related_task_name in task_lookup[task_name].dependencies.all():
        yield related_task_name
        yield from flatten_dependencies(related_task_name, task_lookup)


@dataclass(eq=False, init=False)
class TaskFilter:
    """Small helper to check whether a task should be run."""

    tags: Optional[Set[str]] = None
    task_names: Optional[Set[str]] = None
    related_task_names: Optional[Set[str]] = None

    def __init__(self, tasks: Iterator[Task], context: Context, problem_short: str):
        """Build from context."""

        filtered_tags = context.options.get("tags")
        if filtered_tags is not None:
            self.tags = self.filter_problem_specific(filtered_tags, problem_short)

        # Assemble all tasks and dependencies
        filtered_task_names = context.options.get("tasks")
        if filtered_task_names is not None:
            self.task_names = self.filter_problem_specific(filtered_task_names, problem_short)

            # We also need to pull all dependencies
            self.related_task_names = set()
            task_lookup = {task.name: task for task in tasks}
            for filtered_task_name in self.task_names:
                for related_task_name in flatten_dependencies(filtered_task_name, task_lookup):
                    self.related_task_names.add(related_task_name)

            all_task_names = self.task_names.union(self.related_task_names)

            # Also grab all cleanup steps if they only require filtered tasks
            for task in task_lookup.values():
                if task.stage == TeardownStage.name and task.dependencies.all().issubset(all_task_names):
                    self.related_task_names.add(task.name)

    def __call__(self, task: Task) -> bool:
        """Check if a task should be run."""

        if self.tags is not None:
            if self.tags.isdisjoint(task.tags):
                return False
        if self.task_names is not None:
            if task.name not in self.task_names and task.name not in self.related_task_names:
                return False
        return True

    @property
    def has_effect(self) -> bool:
        return self.tags is not None or self.task_names is not None

    @staticmethod
    def filter_problem_specific(collection: Iterable[str], prefix: str) -> Set[str]:
        """Filter in items prefaced by prefix:xyz as xyz."""

        result = set()
        for item in collection:
            if ":" in item:
                if item.startswith(f"{prefix}:"):
                    result.add(item.split(":", maxsplit=1)[1])
            else:
                result.add(item)
        return result


def _run(
        tasks: List[Task],
        is_visible: Callable[[Task], bool],
        resources: dict,
        report: ProblemReport):
    """Execute sorted tasks, skipping if missing dependencies."""

    log.debug("running tasks")
    for task in tasks:
        log.debug(f"running task {task.name}")

        # Check conditions for whether this case is filtered out, if so report is partial
        if not is_visible(task):
            report.partial = True
            continue

        # If we can't run it, mark as incomplete
        elif not fulfills_dependencies(task, report):
            result = task.Result.incomplete()

        # Run task if not hidden and dependencies are met
        else:
            try:
                result = task.run(resources)

            # Results may be raised
            except Result as r:
                result = r

            # Check if the result is the right type
            if not isinstance(result, task.Result):
                raise GraderException(f"expected result type {task.Result.kind} from {task.name} in {task.source}")

        result.task = task
        report.add(result)


@dataclass(eq=False)
class Grader:
    """A main class for grading runtime."""

    setup: SetupStage = field(default_factory=SetupStage)
    test: TestStage = field(default_factory=TestStage)
    teardown: TeardownStage = field(default_factory=TeardownStage)

    # Populated on import
    problem: "GradingProblem" = field(init=False)

    @property
    def stages(self) -> Tuple[GraderStage, ...]:
        return self.setup, self.test, self.teardown

    @property
    def tasks(self) -> Iterator[Task]:
        yield from self.setup.tasks
        yield from self.test.tasks
        yield from self.teardown.tasks

    def check(self):
        """Topologically sort tasks, checking for cycles."""

        # Check dependencies
        log.debug("sorting grader tasks by dependency")
        topological_sort(stage.tasks for stage in self.stages)

    def run(self, context: Context, submission: Submission) -> ProblemReport:
        """Build and test."""

        log.debug("setting up runtime")

        # Resources
        resources = dict(context=context, submission=submission, problem=self.problem)
        resources.update(resources=resources)

        # Create the filter
        is_visible = TaskFilter(self.tasks, context, self.problem.short)

        # Final report
        report = ProblemReport.create(self.problem)

        # Run each stage
        for stage in self.stages:
            if len(stage.tasks) > 0:
                log.debug(f"starting stage {stage.name}")
                _run(stage.tasks, is_visible, resources, report)
            else:
                log.debug(f"no tasks for stage {stage.name}")

        return report
