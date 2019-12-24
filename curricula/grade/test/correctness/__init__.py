from ...task import Result


class CorrectnessResult(Result):
    """The result of a correctness case."""

    kind = "correctness"

    def __init__(self, passed: bool, complete: bool = True, **details):
        super().__init__(complete=complete, passed=passed, details=details)
