from typing import Callable, Generic, TypeVar, Dict
from dataclasses import dataclass, field

from .resource import Resource


T = TypeVar("T")
Runnable = Callable[[dict], T]


@dataclass
class Task(Generic[T]):
    """Superclass for check, build, run."""

    name: str
    runnable: Runnable[T]
    details: dict = field(default_factory=dict)

    def __hash__(self):
        return id(self)

    def run(self, resources: Dict[str, "Resource"]) -> T:
        """Do the dependency injection for the runnable."""

        return self.runnable(**resources)
