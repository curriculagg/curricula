from typing import Callable

from grade.test import Result, Test


class ComplexityResult(Result):
    """The result of a correctness case."""

    constrained: bool

    def __init__(self, constrained: bool):
        super().__init__()
        self.constrained = constrained

    def __str__(self):
        return "meets complexity constraint" if self.constrained else "failed to meet complexity constraint"


ComplexityRunnable = Callable[..., ComplexityResult]


class ComplexityTest(Test):
    """A test subclassed for a correctness runnable."""

    runnable: ComplexityRunnable

    def __init__(self, name: str, runnable: ComplexityRunnable, **details):
        super().__init__(name, runnable, **details)
