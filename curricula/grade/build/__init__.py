from dataclasses import dataclass, field

from ..task import Result, Runnable
from ..resource import Executable


@dataclass
class BuildResult(Result):
    """Returned from a build task."""

    details: dict = field(default_factory=dict)

    def __init__(self, passed: bool, complete: bool = True, **details):
        super().__init__(complete=complete, passed=passed)
        self.details = details

    def dump(self) -> dict:
        dump = super().dump()
        dump.update(kind="build", details=self.details)
        return dump


Buildable = Runnable[Executable]
