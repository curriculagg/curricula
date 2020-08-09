import jinja2

from dataclasses import dataclass
from pathlib import Path
from typing import List, Callable, Union, Optional, Tuple, TypeVar

from ..shared import Files, Templates
from ..library import files
from ..log import log

from .models import CompilationProblem, CompilationAssignment
from .framework import Configuration, Context

__all__ = (
    "get_readme_path",
    "get_readme",
    "has_readme",
    "ReadmeBuilder",
    "DirectoryMerger",
    "DirectoryAggregator")


def get_readme_path(relative_path: Union[str, Path] = None):
    """Return the expected README.md path."""

    if relative_path is None:
        return Path(Files.README)
    if isinstance(relative_path, str):
        relative_path = Path(relative_path)
    return relative_path.joinpath(Files.README)


@jinja2.environmentfilter
def get_readme(
        environment: jinja2.Environment,
        item: Union[CompilationProblem, CompilationAssignment],
        relative_path: str = None) -> str:
    """Render a README with options for nested path."""

    readme_path = get_readme_path(relative_path).as_posix()

    try:
        if isinstance(item, CompilationAssignment):
            path = f"assignment:{readme_path}"
            data = dict(assignment=item)
        elif isinstance(item, CompilationProblem):
            path = f"problem/{item.short}:{readme_path}"
            data = dict(assignment=item.assignment, problem=item)
        else:
            raise ValueError("invalid item passed to get_readme")
        return environment.get_template(path).render(**data)

    except jinja2.exceptions.TemplateNotFound:
        log.error(f"error finding problem/{item.short}:{readme_path}")
        return ""


def has_readme(item: Union[CompilationProblem, CompilationAssignment], relative_path: str = None) -> bool:
    """Check whether a problem has a solution README."""

    return item.path.joinpath(relative_path or "", Files.README).exists()


T = TypeVar("T")


@dataclass(eq=False)
class ReadmeBuilder:
    """Compose a README based on an assignment and its problems."""

    configuration: Configuration
    readme_relative_path: Path
    template_relative_path: Path
    destination_path: Path

    def __post_init__(self):
        """Set destination to exact path."""

        if self.destination_path.parts[-1].lower() != Files.README.lower():
            self.destination_path = self.destination_path.joinpath(Files.README)

    def run(self, assignment: CompilationAssignment, context: Context) -> Path:
        """Render the template returning the written path."""

        log.debug(f"building {self.readme_relative_path}/README.md to {self.destination_path}")
        template_path = self.template_relative_path.joinpath(Templates.ASSIGNMENT)
        template = context.environment.get_template(f"template:compile/{template_path.as_posix()}")
        with self.destination_path.open("w") as file:
            file.write(template.render(assignment=assignment))
        return self.destination_path

    def should_run(self, assignment: CompilationAssignment, context: Context):
        """Check if any paths are used by this builder."""

        if context.paths_modified is None or context.indices_modified:
            return True

        # Check if a template has been modified
        for path in context.paths_modified:
            if files.contains(self.configuration.custom_template_path, path):
                return True

        # Check if a README has been modified
        readme_path = get_readme_path(self.readme_relative_path)
        used_paths = {assignment.path.joinpath(readme_path).resolve()}
        for problem in assignment.problems:
            used_paths.add(problem.path.joinpath(readme_path).resolve())

        return len(context.paths_modified.intersection(used_paths)) > 0

    def run_if_should(self, assignment: CompilationAssignment, context: Context) -> Tuple[bool, Optional[Path]]:
        """Run if any test_paths are used."""

        if self.should_run(assignment, context):
            return True, self.run(assignment, context)
        return False, None


class DirectoryShouldRun:
    """Shared uses for merger and aggregator."""

    contents_relative_path: Path
    run: Callable[[CompilationAssignment], T]
    should_run: Callable[[CompilationAssignment, Context], bool]

    def should_run(self, assignment: CompilationAssignment, context: Context):
        """Check if any paths are used by this builder."""

        if context.paths_modified is None or context.indices_modified:
            return True

        paths = [assignment.path.joinpath(self.contents_relative_path)]
        for problem in assignment.problems:
            paths.append(assignment.path.joinpath(problem.relative_path, self.contents_relative_path).absolute())

        for path_modified in context.paths_modified:
            for path in paths:
                if files.contains(path, path_modified):
                    return True

        return False

    def run_if_should(self, assignment: CompilationAssignment, context: Context) -> Tuple[bool, T]:
        """Run if any test_paths are used."""

        if self.should_run(assignment, context):
            return True, self.run(assignment)
        return False, None


@dataclass(eq=False)
class DirectoryMerger(DirectoryShouldRun):
    """Merges a set of directories into one."""

    contents_relative_path: Path
    destination_path: Path
    filter_problems: Optional[Callable[[CompilationProblem], bool]] = None

    def run(self, assignment: CompilationAssignment):
        """Merge directory contents."""

        log.debug(f"merging directories {self.contents_relative_path} to {self.destination_path}")

        files.replace_directory(self.destination_path)

        # First copy any assignment-wide resources
        assignment_contents_path = assignment.path.joinpath(self.contents_relative_path)
        if assignment_contents_path.is_dir():
            files.copy_directory(assignment_contents_path, self.destination_path)

        # Overwrite with problem contents, enable filtration
        for problem in filter(self.filter_problems, assignment.problems):
            problem_contents_path = problem.path.joinpath(self.contents_relative_path)
            if problem_contents_path.is_dir():
                files.copy_directory(problem_contents_path, self.destination_path, merge=True)


@dataclass(eq=False)
class DirectoryAggregator(DirectoryShouldRun):
    """Aggregates directories into a single parent."""

    contents_relative_path: Path
    destination_path: Path
    filter_problems: Optional[Callable[[CompilationProblem], bool]] = None
    directory_name: Optional[Callable[[CompilationProblem], str]] = None

    def run(self, assignment: CompilationAssignment) -> List[Path]:
        """Aggregate contents."""

        log.debug(f"aggregating {self.contents_relative_path} to {self.destination_path}")

        files.replace_directory(self.destination_path)

        # First compile assignment-wide assets
        assignment_contents_path = assignment.path.joinpath(self.contents_relative_path)
        if assignment_contents_path.exists():
            files.copy_directory(assignment_contents_path, self.destination_path)

        directory_name = self.directory_name or (lambda p: p.relative_path)

        # Copy per problem, enable filtration
        copied_paths = []
        for problem in filter(self.filter_problems, assignment.problems):
            problem_contents_path = problem.path.joinpath(self.contents_relative_path)
            if problem_contents_path.exists():
                problem_destination_path = self.destination_path.joinpath(directory_name(problem))
                copied_paths.append(problem_destination_path)
                files.copy_directory(problem_contents_path, problem_destination_path)

        return copied_paths
