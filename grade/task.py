import abc
from typing import Callable, Dict, TypeVar, Generic
from dataclasses import dataclass, field, asdict

from .resource import Resource, inject


@dataclass
class Result(abc.ABC):
    """The result of a test."""

    def dump(self) -> dict:
        """Return the result as JSON."""

        return asdict(self)


T = TypeVar("T")
Runnable = Callable[[dict], T]


@dataclass
class Task(Generic[T]):
    """Superclass for check, build, run."""

    name: str
    runnable: Runnable[T]
    details: dict = field(default_factory=dict)

    def run(self, resources: Dict[str, Resource]) -> T:
        """Do the dependency injection for the runnable."""

        return self.runnable(**inject(self.runnable, resources))
