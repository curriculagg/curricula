from typing import Set, Optional, Callable
from pathlib import Path
from dataclasses import dataclass

from ..resource import File, Executable
from ..library.process import run


Buildable = Callable[..., Executable]


@dataclass
class Build:
    """A build strategy that produces an executable."""

    name: str
    buildable: Buildable
    details: dict

    def run(self, **resources) -> Executable:
        """Run build and return a runnable executable."""

        return self.buildable(**resources)


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

    def build(self, timeout: float = 2.0) -> Executable:
        """Build a project with GCC."""


