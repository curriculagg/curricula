import abc
from typing import Callable, Dict, TypeVar, Generic
from dataclasses import dataclass, field, asdict

from .resource import Resource, inject


@dataclass
class Result(abc.ABC):
    """The result of a test."""

    okay: bool
    task: "Task" = field(init=False)

    def dump(self) -> dict:
        """Return the result as JSON."""

        return dict(okay=self.okay, task=self.task.dump())


T = TypeVar("T")
Runnable = Callable[[dict], T]


@dataclass
class Task(Generic[T]):
    """Superclass for check, build, run."""

    name: str
    description: str
    runnable: Runnable[T]
    details: dict = field(default_factory=dict)

    def run(self, resources: Dict[str, Resource]) -> T:
        """Do the dependency injection for the runnable."""

        result = self.runnable(**inject(self.runnable, resources))
        result.task = self
        return result

    def dump(self):
        """Return the task as JSON serializable."""

        return dict(name=self.name, description=self.description, details=self.details)
