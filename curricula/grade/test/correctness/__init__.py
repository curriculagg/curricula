from dataclasses import dataclass, field

from .. import TestResult
from ...library.process import Runtime


@dataclass
class CorrectnessResult(TestResult):
    """The result of a correctness case."""

    runtime: Runtime
    details: dict = field(default_factory=dict)

    def __init__(self, passed: bool, runtime: Runtime, complete: bool = True, **details):
        super().__init__(complete=complete, passed=passed)
        self.runtime = runtime
        self.details = details

    def __str__(self):
        if self.runtime.error is not None:
            return "{} in {} seconds".format(self.runtime.error, self.runtime.elapsed)
        return "{} in {} seconds".format(
            "passed" if self.passed else "failed",
            round(self.runtime.elapsed, 5))

    def dump(self) -> dict:
        dump = super().dump()
        dump.update(kind="correctness", runtime=self.runtime.dump(), details=self.details)
        return dump
