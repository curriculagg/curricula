from dataclasses import dataclass, field

from ..task import Task, Result


@dataclass
class CheckResult(Result):
    """Result of a submission check."""

    details: dict = field(default_factory=dict)

    def __init__(self, okay: bool, **details):
        super().__init__(okay)
        self.details = details

    def dump(self):
        dump = super().dump()
        dump.update(kind="check", details=self.details)
        return dump


@dataclass
class Check(Task[CheckResult]):
    """Add required, fails if true and valid is false."""

    required: bool = field(init=False)

    def __post_init__(self):
        self.required = self.details.pop("required", False)
