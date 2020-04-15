from typing import Optional

from ....library.process import Runtime
from ....library.valgrind import ValgrindReport
from ...task import Result, Error


class MemoryResult(Result):
    """Result of a memory leak test."""

    kind = "memory"

    runtime: Optional[Runtime]
    error_count: Optional[int]
    leaked_blocks: Optional[int]
    leaked_bytes: Optional[int]

    def __init__(
            self,
            passing: bool,
            runtime: Runtime = None,
            complete: bool = True,
            error_count: int = None,
            leaked_blocks: int = None,
            leaked_bytes: int = None,
            **details):
        """Initialize a memory result."""

        super().__init__(complete=complete, passing=passing, details=details)
        self.runtime = runtime
        self.error_count = error_count
        self.leaked_blocks = leaked_blocks
        self.leaked_bytes = leaked_bytes

        # Create the error with additional data
        if error_count > 0 or leaked_bytes > 0:
            self.error = Error(description=f"leaked {leaked_bytes} bytes with {error_count} errors")

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

    def dump(self) -> dict:
        dump = super().dump()
        dump.update(
            runtime=self.runtime.dump() if self.runtime else None,
            error_count=self.error_count,
            leaked_blocks=self.leaked_blocks,
            leaked_bytes=self.leaked_bytes)
        return dump
