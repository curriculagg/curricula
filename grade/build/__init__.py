from dataclasses import dataclass, field

from ..task import Task, Result, Runnable
from ..resource import Executable


@dataclass
class BuildResult(Result):
    """Returned from a build task."""

    details: dict = field(default_factory=dict)

    def __init__(self, complete: bool, **details):
        super().__init__(complete)
        self.details = details

    def dump(self) -> dict:
        dump = super().dump()
        dump.update(kind="build", details=self.details)
        return dump


Buildable = Runnable[Executable]


@dataclass
class Build(Task[BuildResult]):
    """A build strategy that produces an executable."""

    required: bool = field(init=False)

    def __post_init__(self):
        self.required = self.details.pop("required", False)
