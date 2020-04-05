from ..stage import GraderStage, Registrar
from ..task import Result
from .check import CheckResult
from .build import BuildResult


class SetupResult(Result):
    """Common result for generic tasks."""

    kind = "generic"

    def __init__(self, passed: bool = True, complete: bool = True, **details):
        super().__init__(complete=complete, passed=passed, details=details)


class SetupStage(GraderStage):
    """Setup endpoints."""

    name = "setup"

    def generic(self, **details) -> Registrar:
        """Generic tasks."""

        return self.create_registrar(details, SetupResult)

    def build(self, **details) -> Registrar:
        """Compilation."""

        return self.create_registrar(details, BuildResult)

    def check(self, **details) -> Registrar:
        """Passive checks."""

        return self.create_registrar(details, CheckResult)
