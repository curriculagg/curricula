from typing import Callable

from ..test import Result, Test
from grade.resource import Executable, Runtime
from grade.library.message import Messenger


class Correctness(Result):
    """The result of a correctness case."""

    runtime: Runtime

    def __init__(self, passing: bool, runtime: Runtime):
        super().__init__(passing)
        self.runtime = runtime

    def __str__(self):
        if self.runtime.timeout is not None:
            return "timed out in {} seconds".format(self.runtime.timeout)
        return "{} in {} seconds".format(
            "passed" if self.passing else "failed",
            round(self.runtime.elapsed, 5))


CorrectnessRunnable = Callable[[Executable, Messenger], Correctness]


class CorrectnessTest(Test):
    """A test subclassed for a correctness runnable."""

    runnable: CorrectnessRunnable

    def __init__(self, name: str, runnable: CorrectnessRunnable, **details):
        super().__init__(name, runnable, **details)

    def __call__(self, target: Executable, messenger: Messenger) -> Correctness:
        return self.runnable(target, messenger)
