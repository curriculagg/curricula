from typing import Optional
from dataclasses import dataclass, field
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


@dataclass(init=False)
class CodeResult(Result):
    """The result of a correctness case."""

    description: str = field(init=False)
    location: CodeLocation = field(init=False)

    def __init__(self, complete: bool, passing: bool, description: str, location: CodeLocation, **details):
        super().__init__(complete=complete, passing=passing, details=details)
        self.description = description
        self.location = location
