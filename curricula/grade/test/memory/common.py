from ....library.valgrind import ValgrindReport, run
from ..correctness.common import ExecutableOutputMixin
from . import MemoryResult


class MemoryTest(ExecutableOutputMixin):
    """Runs valgrind on the executable with given parameters."""

    def __call__(self, resources: dict) -> MemoryResult:
        """Check if the output matches."""

        self.resources = resources
        self.details = {}
        result = MemoryResult.from_valgrind_report(self.execute())
        result.details.update(self.details)
        self.resources = None
        self.details = None
        return result

    def execute(self) -> ValgrindReport:
        executable = self.resources[self.executable_name]
        report = run(
            *executable.args,
            *self.resolve("args", default=()),
            stdin=self.resolve("stdin", default=None),
            timeout=self.resolve("timeout", default=None),
            cwd=self.resolve("cwd", default=None))
        return report


class GoogleMemoryTest(MemoryTest):
    """Custom gtest args."""

    def __init__(self, test_name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.args = (test_name,)
