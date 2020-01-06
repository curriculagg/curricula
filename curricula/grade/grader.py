import itertools
from typing import List, Dict, Iterable
from dataclasses import dataclass, field

from .report import ProblemReport
from .task import Task
from .stage import GraderStage
from ..log import log

from .setup import SetupStage
from .test import TestStage
from .teardown import TeardownStage
from .configuration.sandbox import SandboxConfiguration
from .configuration.output import OutputConfiguration


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


def topological_sort(stage_tasks: Iterable[List[Task]]):
    """Order tasks by dependency."""

    lookup = {}
    marks = {}
    for tasks in stage_tasks:
        result = []
        for task in tasks:
            marks[task] = 0
            lookup[task.name] = task
        for task in tasks:
            if marks[task] != 2:
                topological_sort_visit(task, lookup, marks, result)
        tasks.clear()
        tasks.extend(result)


def collapse_tasks(stages: Iterable[GraderStage]) -> Iterable[Task]:
    """Wrapper for topological_sort."""

    return itertools.chain(*(stage.tasks for stage in stages))


def fulfills_dependencies(task: Task, report: ProblemReport):
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


@dataclass(eq=False)
class Grader:
    """A main class for grading runtime."""

    setup: SetupStage = field(default_factory=SetupStage)
    test: TestStage = field(default_factory=TestStage)
    teardown: TeardownStage = field(default_factory=TeardownStage)

    sandbox: SandboxConfiguration = field(default_factory=SandboxConfiguration)
    output: OutputConfiguration = field(default_factory=OutputConfiguration)

    @property
    def stages(self):
        return self.setup, self.test, self.teardown

    def check(self):
        """Topologically sort tasks, checking for cycles."""

        # Check dependencies
        log.debug("sorting grader tasks by dependency")
        topological_sort(stage.tasks for stage in self.stages)

        # Check task details
        for task in collapse_tasks(self.stages):
            self.output.check_task(task)

    def __run(self, tasks: List[Task], report: ProblemReport, resources: dict):
        """Execute sorted tasks, skipping if missing dependencies."""

        log.debug("running tasks")
        for task in tasks:
            log.debug(f"running task {task.name}")

            # Check conditions for whether this case is visible
            hidden = sanity_enabled_and_not_sanity(task, resources)

            # Run task if not hidden and dependencies are met
            run_task = not hidden and fulfills_dependencies(task, report)
            result = task.run(resources) if run_task else task.result_type.incomplete()
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

        return {task.name: task.dump() for task in collapse_tasks(self.stages)}
