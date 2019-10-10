import abc
import inspect
from typing import Dict, TypeVar, Generic, Any, Collection
from dataclasses import dataclass, field


@dataclass
class Result(abc.ABC):
    """The result of a test."""

    complete: bool
    passed: bool
    task: "Task" = field(init=False)

    def __str__(self):
        return "passed" if self.complete and self.passed else "failed"

    def dump(self) -> dict:
        return dict(complete=self.complete, passed=self.passed, task=self.task.name)


class Incomplete(Result):
    """Used to represent a task that was never run."""

    def __init__(self, task: "Task"):
        self.task = task
        self.complete = False
        self.passed = False

    def dump(self) -> dict:
        return dict(
            complete=False,
            passed=False,
            details=dict(error="not completed because a dependency failed"))


TResult = TypeVar("TResult", bound=Result)


class Runnable(Generic[TResult]):
    def __call__(self, **kwargs) -> TResult:
        ...


def inject(resources: dict, runnable: Runnable[TResult]) -> TResult:
    """Build injection map for method."""

    dependencies = {}
    for name, parameter in inspect.signature(runnable).parameters.items():
        dependency = resources.get(name, parameter.default)
        assert dependency != parameter.empty, "could not satisfy dependency {}".format(name)
        dependencies[name] = dependency
    return runnable(**dependencies)


@dataclass
class Task(Generic[TResult]):
    """Superclass for check, build, run."""

    name: str
    description: str
    kind: str
    dependencies: Collection[str]
    runnable: Runnable[Result]
    details: dict

    def __str__(self):
        return self.name

    def __hash__(self):
        return id(self)

    def run(self, resources: Dict[str, Any]) -> TResult:
        """Do the dependency injection for the runnable."""

        result = inject(resources, self.runnable)
        if result is not None:
            result.task = self
        return result

    def dump(self):
        """Return the task as JSON serializable."""

        return dict(
            name=self.name,
            description=self.description,
            kind=self.kind,
            dependencies=self.dependencies,
            details=self.details)
