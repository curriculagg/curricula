from dataclasses import dataclass, field

from ..task import Task, Result


@dataclass
class CheckResult(Result):
    """Result of a submission check."""

    valid: bool
    details: dict = field(default_factory=dict)

    def __init__(self, valid: bool, **details):
        self.valid = valid
        self.details = details


@dataclass
class Check(Task[CheckResult]):
    pass
