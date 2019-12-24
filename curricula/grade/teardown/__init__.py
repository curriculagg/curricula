from ..stage import GraderStage, Registrar
from .cleanup import CleanupResult


class TeardownStage(GraderStage):
    """Teardown endpoints."""

    name = "teardown"

    def cleanup(self, **details) -> Registrar:
        """Deleting files."""

        return self.create_registrar(details, CleanupResult)
