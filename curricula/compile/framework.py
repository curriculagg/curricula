import abc

import jinja2

from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Set, Optional, Type, List

from .models import CompilationAssignment
from ..log import log


@dataclass(repr=False, eq=False)
class Configuration:
    """Build context.

    The build context is simply a container for information about the
    build that's passed to each step.
    """

    assignment_path: Path
    artifacts_path: Path
    custom_template_path: Path
    options: Dict[str, str]

    def __post_init__(self):
        if self.custom_template_path is not None:
            log.info(f"custom template path is {self.custom_template_path}")


@dataclass(repr=False, eq=False)
class Context:
    """Details generated at compile time."""

    environment: jinja2.Environment
    indices_modified: bool = False
    paths_modified: Optional[Set[Path]] = None


@dataclass(repr=False, eq=False)
class UnitResult:
    """Compilation result."""

    compiled: bool = False
    tags: Set[str] = field(default_factory=set)


@dataclass(repr=False, eq=False)
class TargetResult:
    """Aggregated compilation results."""

    data: Dict[str, UnitResult] = field(default_factory=dict, init=False)

    def __setitem__(self, key: str, value: UnitResult):
        self.data[key] = value

    def __getitem__(self, item: str):
        return self.data[item]


class Unit(abc.ABC):
    """An independent component of the compilation process."""

    name: str
    configuration: Configuration

    def __init__(self, configuration: Configuration):
        self.configuration = configuration

    @abc.abstractmethod
    def compile(self, assignment: CompilationAssignment, context: Context) -> UnitResult:
        """Compile the unit given the context."""


class Workflow(abc.ABC):
    """Invoked after compilation."""

    configuration: Configuration

    def __init__(self, configuration: Configuration):
        self.configuration = configuration

    @abc.abstractmethod
    def run(self, assignment: CompilationAssignment, result: TargetResult):
        """Invoked after compilation."""


class Target:
    """A complete compilation target."""

    configuration: Configuration
    units: Dict[str, Unit]
    workflows: List[Workflow]

    def __init__(self, configuration: Configuration):
        """Set configuration reference."""

        self.configuration = configuration
        self.units = dict()
        self.workflows = list()

    def unit(self, unit_type: Type[Unit]):
        """Add a unit by its constructor."""

        self.units[unit_type.name] = unit_type(self.configuration)

    def workflow(self, workflow_type: Type[Workflow]):
        """Add a workflow."""

        self.workflows.append(workflow_type(self.configuration))

    def compile(self, assignment: CompilationAssignment, context: Context) -> TargetResult:
        """Compile and return results."""

        result = TargetResult()
        for unit_name, unit in self.units.items():
            result[unit_name] = unit.compile(assignment, context)
        for workflow in self.workflows:
            workflow.run(assignment, result)
        return result
