from ..stage import GraderStage, Registrar
from ..task import GenericResult
from .check import CheckResult
from .build import BuildResult


class SetupStage(GraderStage):
    """Setup endpoints."""

    name = "setup"

    def generic(self, **details) -> Registrar:
        """Generic tasks."""

        return self.create_registrar(details, GenericResult)

    def build(self, **details) -> Registrar:
        """Compilation."""

        return self.create_registrar(details, BuildResult)

    def check(self, **details) -> Registrar:
        """Passive checks."""

        return self.create_registrar(details, CheckResult)
