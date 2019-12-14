from dataclasses import dataclass, field

from .. import TestResult

# TODO: this is getting fucked up


@dataclass
class CorrectnessResult(TestResult):
    """The result of a correctness case."""

    details: dict = field(default_factory=dict)

    def __init__(self, passed: bool, complete: bool = True, **details):
        super().__init__(complete=complete, passed=passed)
        self.details = details

    def __str__(self):
        runtime = self.details.get("runtime")
        passed_text = "passed" if self.passed else "failed"
        if runtime is not None:
            if runtime.error is not None:
                return f"{runtime.error} in {runtime.elapsed} seconds"
            return f"{passed_text} in {runtime.elapsed} seconds"
        return passed_text

    def dump(self) -> dict:
        dump = super().dump()
        details = self.details.copy()
        runtime = self.details.get("runtime")
        if runtime is not None:
            details["runtime"] = runtime.dump()
        dump.update(kind="correctness", details=details)
        return dump
