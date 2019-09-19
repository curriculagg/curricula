from dataclasses import dataclass

from grade.test import Result
from grade.library.process import Runtime


@dataclass
class CorrectnessResult(Result):
    """The result of a correctness case."""

    runtime: Runtime

    def __str__(self):
        if self.runtime.timeout is not None:
            return "timed out in {} seconds".format(self.runtime.timeout)
        return "{} in {} seconds".format(
            "passed" if self.okay else "failed",
            round(self.runtime.elapsed, 5))

    def dump(self) -> dict:
        dump = super().dump()
        dump.update(kind="test.correctness", runtime=self.runtime.dump())
        return dump
