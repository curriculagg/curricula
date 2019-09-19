from typing import Optional
from dataclasses import dataclass

from ...library.process import Runtime
from ...library.valgrind import ValgrindReport
from .. import TestResult


@dataclass
class MemoryResult(TestResult):
    """Result of a memory leak test."""

    runtime: Runtime
    error_count: Optional[int] = None
    leaked_blocks: Optional[int] = None
    leaked_bytes: Optional[int] = None

    @classmethod
    def from_valgrind_report(cls, report: ValgrindReport) -> "MemoryResult":
        """Generate a memory test result from a valgrind report."""

        if report.errors is None:
            return cls(False, report.runtime)
        blocks_leaked, bytes_leaked = report.memory_lost()
        return cls(bytes_leaked == 0, report.runtime, len(report.errors), blocks_leaked, bytes_leaked)

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
            runtime=self.runtime.dump(),
            error_count=self.error_count,
            leaked_blocks=self.leaked_blocks,
            leaked_bytes=self.leaked_bytes)
        return dump
