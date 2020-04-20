from ..stage import GraderStage, Registrar
from ..task import Result, Error
from .check import CheckResult
from .build import BuildResult


class SetupResult(Result):
    """Common result for generic tasks."""

    kind = "generic"

    def __init__(self, passing: bool = True, complete: bool = True, error: Error = None, **details):
        super().__init__(complete=complete, passing=passing, error=error, details=details)


class SetupStage(GraderStage):
    """Setup endpoints."""

    name = "setup"

    def generic(self, **details) -> Registrar:
        """Generic tasks."""

        return self.registrar(details, SetupResult)

    def build(self, **details) -> Registrar:
        """Compilation."""

        return self.registrar(details, BuildResult)

    def check(self, **details) -> Registrar:
        """Passive checks."""

        return self.registrar(details, CheckResult)
