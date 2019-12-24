from ...task import Result


class CorrectnessResult(Result):
    """The result of a correctness case."""

    kind = "correctness"

    def __init__(self, passed: bool, complete: bool = True, **details):
        super().__init__(complete=complete, passed=passed, details=details)

    def dump(self) -> dict:
        dump = super().dump()
        details = self.details.copy()
        runtime = self.details.get("runtime")
        if runtime is not None:
            details["runtime"] = runtime.dump()
        return dump
