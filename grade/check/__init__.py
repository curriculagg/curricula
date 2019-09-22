from dataclasses import dataclass

from ..task import Result


@dataclass
class CheckResult(Result):
    """Result of a submission check."""

    details: dict

    def __init__(self, passed: bool, complete=True, **details):
        super().__init__(complete=complete, passed=passed)
        self.details = details

    def dump(self):
        dump = super().dump()
        dump.update(kind="check", details=self.details)
        return dump
