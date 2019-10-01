import abc
import inspect
from typing import Dict, TypeVar, Generic, Any
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
        return dict(complete=self.complete, passed=self.passed, task=self.task.dump())


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
            task=self.task.dump(),
            details=dict(error="not completed because a prior required task failed"))


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
    required: bool
    runnable: Runnable[Result]
    details: dict

    def __str__(self):
        return self.name

    def __hash__(self):
        return id(self)

    def run(self, resources: Dict[str, Any]) -> TResult:
        """Do the dependency injection for the runnable."""

        result = inject(resources, self.runnable)
        result.task = self
        return result

    def dump(self):
        """Return the task as JSON serializable."""

        return dict(
            name=self.name,
            description=self.description,
            kind=self.kind,
            required=self.required,
            details=self.details)
