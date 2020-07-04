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


def sanity_enabled_and_not_sanity(task: Task, resources: dict):
    """Convenience."""

    context = resources["context"]
    if "sanity" not in context.options or not context.options["sanity"]:
        return False
    if "sanity" in task.details and task.details["sanity"]:
        return False
    return True


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

    def __run(self, tasks: List[Task], report: ProblemReport, resources: dict):
        """Execute sorted tasks, skipping if missing dependencies."""

        log.debug("running tasks")
        for task in tasks:
            log.debug(f"running task {task.name}")

            # Check conditions for whether this case is visible
            hidden = sanity_enabled_and_not_sanity(task, resources)

            # Run task if not hidden and dependencies are met
            if not hidden and fulfills_dependencies(task, report):
                try:
                    result = task.run(resources)

                # Results may be raised
                except Result as r:
                    result = r

                # Check if the result is the right type
                if not isinstance(result, task.Result):
                    raise GraderException(f"expected result type {task.Result.kind} from {task.name} in {task.source}")

            # Otherwise take an incomplete result
            else:
                result = task.Result.incomplete()

            result.task = task

            # Check result
            self.output.check_result(result)

            # Add to report
            report.add(result, hidden=hidden)

    def run(self, **resources) -> ProblemReport:
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
                self.__run(stage.tasks, report, resources)
            else:
                log.debug(f"no tasks for stage {stage.name}")

        # Revert, trusting plugin
        log.debug("reverting configurators")
        self.sandbox.revert()

        return report

    def dump(self) -> dict:
        """Dump the tasks to something JSON serializable."""

        return {task.name: task.dump() for task in self.tasks}
