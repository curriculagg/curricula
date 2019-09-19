import abc
from typing import Callable, Dict, TypeVar, Generic
from dataclasses import dataclass, field

from .resource import Resource, inject


@dataclass
class Result(abc.ABC):
    """The result of a test."""

    okay: bool
    task: "Task" = field(init=False)

    def dump(self) -> dict:
        """Return the result as JSON."""

        return dict(okay=self.okay, task=self.task.dump())


TResult = TypeVar("TResult", bound=Result)


class Runnable(Generic[TResult]):
    def __call__(self, **kwargs) -> TResult:
        ...


@dataclass
class Task(Generic[TResult]):
    """Superclass for check, build, run."""

    name: str
    description: str
    runnable: Runnable[Result]
    details: dict = field(default_factory=dict)

    def run(self, resources: Dict[str, Resource]) -> TResult:
        """Do the dependency injection for the runnable."""

        result = inject(resources, self.runnable)
        result.task = self
        return result

    def dump(self):
        """Return the task as JSON serializable."""

        return dict(name=self.name, description=self.description, details=self.details)
