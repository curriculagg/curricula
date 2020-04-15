from ..stage import GraderStage
from .code import CodeResult
from .complexity import ComplexityResult
from .correctness import CorrectnessResult
from .memory import MemoryResult


class TestStage(GraderStage):
    """Test endpoints."""

    name = "test"

    def code(self, **details):
        """Code quality."""

        return self.registrar(details, CodeResult)

    def complexity(self, **details):
        """Runtime complexity."""

        return self.registrar(details, ComplexityResult)

    def correctness(self, **details):
        """Program correctness."""

        return self.registrar(details, CorrectnessResult)

    def memory(self, **details):
        """Resource allocation."""

        return self.registrar(details, MemoryResult)
