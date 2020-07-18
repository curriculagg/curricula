import abc
from decimal import Decimal

from ..task import Result
from ..stage import GraderStage
from .code import CodeResult
from .complexity import ComplexityResult
from .correctness import CorrectnessResult
from .memory import MemoryResult


class Test(abc.ABC):
    """Convenience class for building dynamic test objects."""

    def __call__(self, *args, **kwargs) -> Result:
        """Should behave like a standard runnable."""


class TestStage(GraderStage):
    """Test endpoints."""

    name = "test"

    @property
    def weight(self) -> Decimal:
        """Get the cumulative weight of all tasks."""

        return sum(task.weight for task in self.tasks)

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
