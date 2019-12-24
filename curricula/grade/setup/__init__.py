from ..stage import GraderStage, Registrar
from .check import CheckResult
from .build import BuildResult


class SetupStage(GraderStage):
    """Setup endpoints."""

    name = "setup"

    def build(self, **details) -> Registrar:
        """Compilation."""

        return self.create_registrar(details, BuildResult)

    def check(self, **details) -> Registrar:
        """Passive checks."""

        return self.create_registrar(details, CheckResult)
