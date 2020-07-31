import abc

import jinja2

from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Set, Optional

from .models import CompilationAssignment


@dataclass(repr=False, eq=False)
class Configuration:
    """Build context.

    The build context is simply a container for information about the
    build that's passed to each step.
    """

    assignment_path: Path
    artifacts_path: Path
    options: Dict[str, str]


@dataclass(repr=False, eq=False)
class Context:
    """Details generated at compile time."""

    environment: jinja2.Environment
    paths_modified: Optional[Set[Path]]


class CompilationUnit(abc.ABC):
    """An independent component of the compilation process."""

    configuration: Configuration

    def __init__(self, configuration: Configuration):
        self.configuration = configuration

    @abc.abstractmethod
    def compile(self, assignment: CompilationAssignment, context: Context):
        """Compile the unit given the context."""


class Compilation(abc.ABC):
    """A compilation unit container."""

    configuration: Configuration

    def __init__(self, configuration: Configuration):
        self.configuration = configuration

    def compile(self, paths_modified: Set[Path]):
        """Compile all units."""
