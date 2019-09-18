from typing import Set, Optional
from pathlib import Path
from dataclasses import dataclass

from ..resource import File, Executable


@dataclass
class Build:
    """A build strategy that produces an executable."""

    def build(self) -> Executable:
        """Run build and return a runnable executable."""


@dataclass
class GccBuild(Build):
    """Build with a GCC command."""

    file: File
    flags: Optional[Set[str]] = None
    out: str = None

    def __post_init__(self):
        """Update out if not set."""

        if self.out is None:
            self.out = Path(self.file.path).parts[-1].rsplit(".", maxsplit=1)[0]

    def build(self) -> Executable:
        pass
