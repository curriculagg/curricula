from ..task import Result
from ..stage import GraderStage, Registrar
from .cleanup import CleanupResult


class TeardownResult(Result):
    """Common result for generic tasks."""

    kind = "generic"

    def __init__(self, passing: bool = True, complete: bool = True, **details):
        super().__init__(complete=complete, passing=passing, details=details)


class TeardownStage(GraderStage):
    """Teardown endpoints."""

    name = "teardown"

    def generic(self, **details) -> Registrar:
        """Generic tasks."""

        return self.registrar(details, TeardownResult)

    def cleanup(self, **details) -> Registrar:
        """Deleting files."""

        return self.registrar(details, CleanupResult)
