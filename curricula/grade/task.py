import abc
import inspect
from typing import Dict, TypeVar, Generic, Any, Collection, Type
from dataclasses import dataclass, field

from ..log import log


@dataclass(init=False)
class Result(Exception, abc.ABC):
    """The result of a test."""

    complete: bool
    passed: bool
    details: dict

    kind: str = field(init=False)
    task: "Task" = field(init=False)

    def __init__(self, complete: bool, passed: bool, details: dict):
        self.complete = complete
        self.passed = passed
        self.details = details

    def __str__(self):
        return "passed" if self.complete and self.passed else "failed"

    def dump(self) -> dict:
        return dict(
            complete=self.complete,
            passed=self.passed,
            task=self.task.name,
            details=self.details)

    @classmethod
    def incomplete(cls):
        return cls(complete=False, passed=False)


TResult = TypeVar("TResult", bound=Result)


class Runnable(Generic[TResult]):
    def __call__(self, **kwargs) -> TResult:
        ...


def inject(resources: dict, runnable: Runnable[TResult]) -> TResult:
    """Build injection map for method."""

    dependencies = {}
    for name, parameter in inspect.signature(runnable).parameters.items():
        dependency = resources.get(name, parameter.default)
        if dependency == parameter.empty:
            raise ValueError(f"could not satisfy dependency {name}")
        dependencies[name] = dependency
    return runnable(**dependencies)


@dataclass
class Task(Generic[TResult]):
    """Superclass for check, build, run."""

    name: str
    description: str
    stage: str
    kind: str
    dependencies: Collection[str]
    runnable: Runnable[Result]
    details: dict
    result_type: Type[Result]

    def __str__(self):
        return self.name

    def __hash__(self):
        return id(self)

    def run(self, resources: Dict[str, Any]) -> TResult:
        """Do the dependency injection for the runnable."""

        try:
            result = inject(resources, self.runnable)
        except ValueError as error:
            raise ValueError(f"caught in {self.name}: {error}")

        if result is None:
            log.debug(f"task {self.name} did not return a result")
            result = self.result_type()
        return result

    def dump(self):
        """Return the task as JSON serializable."""

        return dict(
            name=self.name,
            description=self.description,
            stage=self.stage,
            kind=self.kind,
            dependencies=self.dependencies,
            details=self.details)
