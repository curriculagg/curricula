from .. import TestResult


class ComplexityResult(TestResult):
    """The result of a correctness case."""

    constrained: bool

    def __init__(self, constrained: bool):
        super().__init__()
        self.constrained = constrained

    def __str__(self):
        return "meets complexity constraint" if self.constrained else "failed to meet complexity constraint"
