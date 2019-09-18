from typing import Optional
from dataclasses import dataclass, field

from ..task import Task, Result, Runnable
from ..resource import Executable


@dataclass
class BuildResult(Result):
    """Returned from a build task."""

    executable: Optional[Executable]
    details: dict = field(default_factory=dict)

    def __init__(self, executable: Executable = None, **details):
        self.executable = executable
        self.details = details


Buildable = Runnable[Executable]


@dataclass
class Build(Task[BuildResult]):
    """A build strategy that produces an executable."""
