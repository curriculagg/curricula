from dataclasses import dataclass

from ...task import Result


@dataclass(init=False, eq=False)
class CheckResult(Result):
    """Result of a submission check."""

    kind = "check"

    def __init__(self, passed: bool, complete=True, **details):
        super().__init__(complete=complete, passed=passed, details=details)
