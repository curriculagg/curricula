import abc
import inspect
from typing import Dict, TypeVar, Generic, Any, Type, Set
from dataclasses import dataclass, field

from ..log import log

__all__ = ("Error", "Result", "Dependencies", "Task", "Runnable")


@dataclass(eq=False)
class Error:
    """An error raised during a task."""

    description: str
    location: str = None
    suggestion: str = None
    expected: Any = None
    received: Any = None

    def dump(self) -> dict:
        return dict(
            description=self.description,
            location=self.location,
            suggestion=self.suggestion,
            expected=self.expected,
            received=self.received)


@dataclass(init=False, eq=False)
class Result(Exception, abc.ABC):
    """The result of a test."""

    complete: bool
    passing: bool
    details: dict
    error: Error

    kind: str = field(init=False)
    task: "Task" = field(init=False)

    def __init__(self, complete: bool, passing: bool, error: Error = None, details: dict = None):
        """Initialize a new result.

        Details are passed as a dictionary in order to avoid potential
        collisions with normal arguments.
        """

        self.complete = complete
        self.passing = passing
        self.error = error
        self.details = details or dict()

    def dump(self) -> dict:
        """Serialize the result for JSON."""

        return dict(
            complete=self.complete,
            passing=self.passing,
            details=self.details,
            error=self.error.dump() if self.error is not None else self.error,
            task=self.task.name)

    @classmethod
    def incomplete(cls):
        """Return a mock result if the task was not completed."""

        return cls(complete=False, passing=False)


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
        return dict(
            passing=list(self.passing),
            complete=list(self.complete))


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

    Result: Type[Result]

    def __hash__(self):
        """Used for dictionary building."""

        return id(self)

    def inject(self, resources: dict) -> TResult:
        """Build injection map for method."""

        dependencies = {}
        for name, parameter in inspect.signature(self.runnable).parameters.items():
            dependency = resources.get(name, parameter.default)
            if dependency == parameter.empty:
                raise ValueError(f"could not satisfy dependency {name}")
            dependencies[name] = dependency
        return self.runnable(**dependencies)

    def run(self, resources: Dict[str, Any]) -> TResult:
        """Do the dependency injection for the runnable."""

        try:
            result = self.inject(resources)
        except ValueError as error:
            raise ValueError(f"caught in {self.name}: {error}")

        if result is None:
            log.debug(f"task {self.name} did not return a result")
            return self.Result(complete=True, passing=True)

        return result

    def dump(self):
        """Return the task as JSON serializable."""

        return dict(
            name=self.name,
            description=self.description,
            stage=self.stage,
            kind=self.kind,
            dependencies=self.dependencies.dump(),
            details=self.details)
