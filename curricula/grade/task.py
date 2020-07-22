import abc
import inspect
from typing import Dict, TypeVar, Generic, Any, Type, Set
from dataclasses import dataclass, field, asdict
from decimal import Decimal

from ..log import log

__all__ = ("Error", "Result", "Dependencies", "Task", "Runnable")


@dataclass(eq=False)
class Error:
    """An error raised during a task."""

    description: str
    suggestion: str = None
    location: str = None
    traceback: str = None
    expected: Any = None
    received: Any = None

    def dump(self, thin: bool = False) -> dict:
        if thin:
            return dict(description=self.description, suggestion=self.suggestion)
        return asdict(self)

    @classmethod
    def load(cls, data: dict) -> "Error":
        return cls(**data)


@dataclass(init=False, eq=False)
class Result(Exception, abc.ABC):
    """The result of a test."""

    complete: bool
    passing: bool
    details: dict
    error: Error

    kind: str = field(init=False)
    task: "Task" = field(init=False, repr=False)

    def __init__(self, complete: bool, passing: bool, error: Error = None, details: dict = None):
        """Initialize a new result.

        Details are passed as a dictionary in order to avoid potential
        collisions with normal arguments.
        """

        self.complete = complete
        self.passing = passing
        self.error = error
        self.details = details or dict()

    def dump(self, thin: bool = False) -> dict:
        """Serialize the result for JSON."""

        dump = dict(
            complete=self.complete,
            passing=self.passing,
            kind=self.kind,
            error=self.error.dump(thin=thin) if self.error is not None else self.error,
            task=dict(
                name=self.task.name,
                description=self.task.description))
        if not thin:
            dump.update(details=self.details)
        return dump

    @classmethod
    def load(cls, data: dict, task: "Task") -> "Result":
        """Load a result from serialized."""

        data.pop("task")
        kind = data.pop("kind")
        error_data = data.pop("error")
        error = Error.load(error_data) if error_data is not None else None
        self = cls(**data, error=error)
        self.task = task
        self.kind = kind
        return self

    @classmethod
    def incomplete(cls):
        """Return a mock result if the task was not completed."""

        return cls(complete=False, passing=False)

    @classmethod
    def default(cls):
        """Called in special cases if no result is returned."""

        return cls(complete=True, passing=True)


TResult = TypeVar("TResult", bound=Result)


class Runnable(Generic[TResult]):
    """Runnable function that returns some kind of result."""

    def __call__(self, **kwargs) -> TResult:
        """The signature that will receive dependency injection."""


@dataclass(eq=False)
class Dependencies:
    """Task dependencies based on passing or completion."""

    passing: Set[str]
    complete: Set[str]

    @classmethod
    def normalize_from_details(cls, name: str, details: dict) -> Set[str]:
        """Normalize a set of strings."""

        value = details.pop(name, None)
        if value is None:
            return set()
        if isinstance(value, str):
            return {value}
        if isinstance(value, set):
            return value
        return set(value)

    @classmethod
    def from_details(cls, details: dict):
        """Parse from decorator details."""

        return cls(
            passing=cls.normalize_from_details("passing", details),
            complete=cls.normalize_from_details("complete", details))

    def dump(self):
        return dict(passing=list(self.passing), complete=list(self.complete))


@dataclass(eq=False)
class Task(Generic[TResult]):
    """Superclass for check, build, run."""

    name: str
    description: str
    stage: str
    kind: str

    dependencies: Dependencies
    runnable: Runnable[Result]
    details: dict

    weight: Decimal
    source: str
    tags: Set[str]

    Result: Type[Result]

    def run(self, resources: Dict[str, Any]) -> TResult:
        """Do the dependency injection for the runnable."""

        dependencies = {}
        for name, parameter in inspect.signature(self.runnable).parameters.items():
            dependency = resources.get(name, parameter.default)
            if dependency == parameter.empty:
                raise ValueError(f"caught in {self.name}: could not satisfy dependency {name}")
            dependencies[name] = dependency
        result = self.runnable(**dependencies)

        if result is None:
            log.debug(f"task {self.name} did not return a result")
            return self.Result.default()

        return result
