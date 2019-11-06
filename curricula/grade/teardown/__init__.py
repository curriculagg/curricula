from dataclasses import dataclass, field

from ..task import Result


@dataclass
class TeardownResult(Result):
    """The result of a teardown step."""

    details: dict = field(default_factory=dict)

    def __init__(self, passed: bool = True, complete: bool = True, **details):
        super().__init__(complete=complete, passed=passed)
        self.details = details

    def dump(self) -> dict:
        dump = super().dump()
        dump.update(kind="teardown", details=self.details)
        return dump
