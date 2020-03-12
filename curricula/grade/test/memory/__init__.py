from typing import Optional

from ....library.process import Runtime
from ....library.valgrind import ValgrindReport
from ...task import Result


class MemoryResult(Result):
    """Result of a memory leak test."""

    kind = "memory"

    runtime: Optional[Runtime]
    error_count: Optional[int]
    leaked_blocks: Optional[int]
    leaked_bytes: Optional[int]

    def __init__(
            self,
            passed: bool,
            runtime: Runtime = None,
            complete: bool = True,
            error_count: int = None,
            leaked_blocks: int = None,
            leaked_bytes: int = None,
            **details):
        super().__init__(complete=complete, passed=passed, details=details)
        self.runtime = runtime
        self.error_count = error_count
        self.leaked_blocks = leaked_blocks
        self.leaked_bytes = leaked_bytes

    @classmethod
    def from_valgrind_report(cls, report: ValgrindReport, **details) -> "MemoryResult":
        """Generate a memory test result from a valgrind report."""

        if report.errors is None:
            return cls(complete=False, passed=False, runtime=report.runtime)
        leaked_blocks, leaked_bytes = report.memory_lost()
        return cls(
            passed=leaked_bytes == 0 and len(report.errors) == 0,
            runtime=report.runtime,
            error_count=len(report.errors),
            leaked_blocks=leaked_blocks,
            leaked_bytes=leaked_bytes,
            **details)

    def __str__(self):
        if self.leaked_bytes is None:
            return "failed to run"
        if self.leaked_bytes > 0:
            return f"leaked {self.leaked_bytes} bytes"
        if self.error_count > 0:
            return f"encountered {self.error_count} errors"
        return "found no leaked memory"

    def dump(self) -> dict:
        dump = super().dump()
        dump.update(
            runtime=self.runtime.dump() if self.runtime else None,
            error_count=self.error_count,
            leaked_blocks=self.leaked_blocks,
            leaked_bytes=self.leaked_bytes)
        return dump
