from ..stage import GraderStage, Registrar
from ..task import GenericResult
from .cleanup import CleanupResult


class TeardownStage(GraderStage):
    """Teardown endpoints."""

    name = "teardown"

    def generic(self, **details) -> Registrar:
        """Generic tasks."""

        return self.create_registrar(details, GenericResult)

    def cleanup(self, **details) -> Registrar:
        """Deleting files."""

        return self.create_registrar(details, CleanupResult)
