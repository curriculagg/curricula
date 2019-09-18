from dataclasses import dataclass

from ..task import Task, Runnable
from ..resource import Executable


Buildable = Runnable[Executable]


@dataclass
class Build(Task[Executable]):
    """A build strategy that produces an executable."""
