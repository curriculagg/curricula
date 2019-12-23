import abc
import inspect
from typing import Dict, TypeVar, Generic, Any, Collection, Type
from dataclasses import dataclass, field


@dataclass
class Result(abc.ABC):
    """The result of a test."""

    complete: bool
    passed: bool
    details: dict = field(default_factory=dict)

    task: "Task" = field(init=False)

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
    result_type: Type[Result]

    def __str__(self):
        return self.name

    def __hash__(self):
        return id(self)

    def run(self, resources: Dict[str, Any]) -> TResult:
        """Do the dependency injection for the runnable."""

        result = inject(resources, self.runnable)
        assert result, "Task must return a result"
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
