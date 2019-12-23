from typing import Optional
from dataclasses import dataclass
from pathlib import Path

from ...task import Result


@dataclass
class CodeLocation:
    """File, line, column."""

    path: Path
    line: Optional[int] = None
    column: Optional[int] = None

    def __str__(self):
        if self.column:
            return f"{self.path.parts[-1]}:{self.line}.{self.column}"
        if self.line:
            return f"{self.path.parts[-1]}:{self.line}"
        return f"{self.path}"


@dataclass
class CodeResult(Result):
    """The result of a correctness case."""

    description: str
    location: CodeLocation
