from dataclasses import dataclass

from ...task import Result


@dataclass(init=False, eq=False)
class BuildResult(Result):
    """Returned from a build task."""

    kind = "build"

    def __init__(self, passed: bool, complete: bool = True, **details):
        super().__init__(complete=complete, passed=passed, details=details)
