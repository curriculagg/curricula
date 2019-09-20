import abc
import inspect
from typing import Dict, TypeVar, Generic, Any
from dataclasses import dataclass, field


@dataclass
class Result(abc.ABC):
    """The result of a test."""

    complete: bool
    task: "Task" = field(init=False)

    def dump(self) -> dict:
        """Return the result as JSON."""

        return dict(complete=self.complete, task=self.task.dump())


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
    runnable: Runnable[Result]
    details: dict = field(default_factory=dict)

    def run(self, resources: Dict[str, Any]) -> TResult:
        """Do the dependency injection for the runnable."""

        result = inject(resources, self.runnable)
        result.task = self
        return result

    def dump(self):
        """Return the task as JSON serializable."""

        return dict(name=self.name, description=self.description, details=self.details)
