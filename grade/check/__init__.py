from dataclasses import dataclass, field

from ..task import Task, Result


@dataclass
class CheckResult(Result):
    """Result of a submission check."""

    passed: bool
    details: dict

    def __init__(self, complete: bool, passed: bool, **details):
        super().__init__(complete)
        self.passed = passed
        self.details = details

    def dump(self):
        dump = super().dump()
        dump.update(passed=self.passed, kind="check", details=self.details)
        return dump


@dataclass
class Check(Task[CheckResult]):
    """Add required, fails if true and valid is false."""

    required: bool = field(init=False)

    def __post_init__(self):
        self.required = self.details.pop("required", False)
