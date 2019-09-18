from dataclasses import dataclass, asdict

from grade.test import Result
from grade.library.process import Runtime


@dataclass
class CorrectnessResult(Result):
    """The result of a correctness case."""

    correct: bool
    runtime: Runtime

    def __str__(self):
        if self.runtime.timeout is not None:
            return "timed out in {} seconds".format(self.runtime.timeout)
        return "{} in {} seconds".format(
            "passed" if self.correct else "failed",
            round(self.runtime.elapsed, 5))

    def dump(self) -> dict:
        return {
            "correct": self.correct,
            "runtime": asdict(self.runtime)
        }
