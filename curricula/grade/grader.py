from typing import List, Tuple, Iterator
from dataclasses import dataclass, field

from .report import ProblemReport
from .task import Task, Result
from .stage import GraderStage
from .exception import GraderException
from ..log import log

from .dependency import topological_sort
from .setup import SetupStage
from .test import TestStage
from .teardown import TeardownStage
from .configuration.sandbox import SandboxConfiguration
from .configuration.output import OutputConfiguration

import typing

if typing.TYPE_CHECKING:
    from .models import GradingProblem


def fulfills_dependencies(task: Task, report: ProblemReport):
    """Convenience."""

    return all((
        all(report.lookup[dependency].passing for dependency in task.dependencies.passing),
        all(report.lookup[dependency].complete for dependency in task.dependencies.complete)))


@dataclass(eq=False)
class Grader:
    """A main class for grading runtime."""

    setup: SetupStage = field(default_factory=SetupStage)
    test: TestStage = field(default_factory=TestStage)
    teardown: TeardownStage = field(default_factory=TeardownStage)

    sandbox: SandboxConfiguration = field(default_factory=SandboxConfiguration)
    output: OutputConfiguration = field(default_factory=OutputConfiguration)

    # Populated internally
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

        # Check task details
        for task in self.tasks:
            self.output.check_task(task)

    def __run(self, tasks: List[Task], report: ProblemReport, resources: dict, options: dict):
        """Execute sorted tasks, skipping if missing dependencies."""

        log.debug("running tasks")
        for task in tasks:
            log.debug(f"running task {task.name}")

            # Check conditions for whether this case is visible
            visible = True
            tags = options.get("tags")
            if tags is not None:
                tags = set(tags)
                if tags.isdisjoint(task.tags):
                    visible = False
            task_names = options.get("tasks")
            if task_names is not None:
                task_names = set(task_names)
                if task.name not in task_names:
                    visible = False

            if not visible:
                result = task.Result.hidden()
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

            # Check result
            self.output.check_result(result)

            # Add to report
            report.add(result)

    def run(self, resources: dict, options: dict) -> ProblemReport:
        """Build and test."""

        log.debug("setting up runtime")
        report = ProblemReport()
        resources.update(report=report, resources=resources)

        # Apply configuration
        log.debug("enabling configurators")
        self.sandbox.apply()

        # Run each stage
        for stage in self.stages:
            if len(stage.tasks) > 0:
                log.debug(f"starting stage {stage.name}")
                self.__run(stage.tasks, report, resources, options)
            else:
                log.debug(f"no tasks for stage {stage.name}")

        # Revert, trusting plugin
        log.debug("reverting configurators")
        self.sandbox.revert()

        return report
