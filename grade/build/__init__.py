from typing import Optional
from dataclasses import dataclass, field

from ..task import Task, Result, Runnable
from ..resource import Executable


@dataclass
class BuildResult(Result):
    """Returned from a build task."""

    executable: Optional[Executable]
    name: Optional[str]
    details: dict = field(default_factory=dict)

    def __init__(self, okay: bool, executable: Executable = None, name: str = None, **details):
        super().__init__(okay)
        self.name = name
        self.executable = executable
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
