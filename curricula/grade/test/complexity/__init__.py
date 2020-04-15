from ...task import Result


class ComplexityResult(Result):
    """The result of a correctness case."""

    kind = "correctness"

    def __init__(self, passing: bool, complete: bool = True, **details):
        super().__init__(complete=complete, passing=passing, details=details)
