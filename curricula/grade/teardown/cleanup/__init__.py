from dataclasses import dataclass

from ...task import Result


@dataclass
class CleanupResult(Result):
    """Deletion of files, deallocation, etc."""

    def __init__(self, passed: bool = True, complete: bool = True, **details):
        super().__init__(complete=complete, passed=passed, details=details)
