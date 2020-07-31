"""A package that provides tools for building assignments.

Curricula's build system takes an assignment composed of a set of a
set of problems, and separates the contents of each into combined
instructions, resources, grading, and solution artifacts. The
structure of an assignment is as follows:

assignment/
| README.md
| assignment.json

The structure of a problem is somewhat similar:

problem/
| README.md
| problem.json
| assets/
| | ...
| grading/
| | README.md
| | tests.py
| | ...
| resources/
| | ...
| solution/
| | README.md
| | ...

Typically, problems are located in a sub-folder assignment/problem/.
However, the problems are linked to assignments in the assignment.json
file via relative path, so the problem directory could be anywhere.
"""

import json
from pathlib import Path
from typing import Set, Optional

from ..shared import Files, Paths, Templates
from ..library.template import jinja2_create_environment
from ..library import files
from ..library.utility import timed
from ..log import log

from .validate import validate
from .content import *
from .models import CompilationProblem, CompilationAssignment
from .compilation import Compilation, CompilationUnit, Context, Configuration


root = Path(__file__).parent.absolute()


class InstructionsCompilationUnit(CompilationUnit):
    """Builds the instructions and assets."""

    output_path: Path
    readme_builder: ReadmeBuilder
    asset_merger: DirectoryMerger

    def __init__(self, configuration: Configuration):
        super().__init__(configuration)
        self.output_path = self.configuration.artifacts_path.joinpath(Paths.INSTRUCTIONS)
        self.readme_builder = ReadmeBuilder(
            configuration=self.configuration,
            readme_relative_path=Paths.DOT,
            template_relative_path=Templates.Instructions.ASSIGNMENT,
            destination_path=self.output_path)
        self.asset_merger = DirectoryMerger(
            contents_relative_path=Paths.ASSETS,
            destination_path=self.output_path.joinpath(Paths.ASSETS))

    def compile_readme(self, assignment: CompilationAssignment, context: Context):
        run, _ = self.readme_builder.run_if_should(assignment, context)
        log.info(f"""instructions: {"built" if run else "skipped"} readme""")

    def merge_assets(self, assignment: CompilationAssignment, context: Context):
        run, _ = self.asset_merger.run_if_should(assignment, context)
        log.info(f"""instructions: {"merged" if run else "skipped"} assets""")

    def compile(self, assignment: CompilationAssignment, context: Context):
        self.output_path.mkdir(exist_ok=True)
        self.compile_readme(assignment, context)
        self.merge_assets(assignment, context)


class ResourcesCompilationUnit(CompilationUnit):
    """Builds the instructions and assets."""

    output_path: Path
    content_aggregator: DirectoryAggregator

    def __init__(self, configuration: Configuration):
        super().__init__(configuration)
        self.output_path = self.configuration.artifacts_path.joinpath(Paths.RESOURCES)
        self.content_aggregator = DirectoryAggregator(
            contents_relative_path=Paths.RESOURCES,
            destination_path=self.output_path,
            directory_name=lambda p: p.short)

    def compile(self, assignment: CompilationAssignment, context: Context):
        run, _ = self.content_aggregator.run_if_should(assignment, context)
        log.info(f"""resources: {"aggregated" if run else "skipped"} resources""")


class SolutionCompilationUnit(CompilationUnit):
    """Creates cheat sheet and solution code."""

    output_path: Path
    readme_builder: ReadmeBuilder
    content_aggregator: DirectoryAggregator

    def __init__(self, configuration: Configuration):
        super().__init__(configuration)
        self.output_path = self.configuration.artifacts_path.joinpath(Paths.SOLUTION)
        self.readme_builder = ReadmeBuilder(
            configuration=self.configuration,
            readme_relative_path=Paths.SOLUTION,
            template_relative_path=Templates.Solution.ASSIGNMENT,
            destination_path=self.output_path)
        self.content_aggregator = DirectoryAggregator(
            contents_relative_path=Paths.SOLUTION,
            destination_path=self.output_path,
            directory_name=lambda p: p.short)

    def compile_readme(self, assignment: CompilationAssignment, context: Context):
        run, _ = self.readme_builder.run_if_should(assignment, context)
        log.info(f"""solution: {"built" if run else "skipped"} readme""")

    def aggregate_contents(self, assignment: CompilationAssignment, context: Context):
        run, copied_paths = self.content_aggregator.run_if_should(assignment, context)
        log.info(f"""solution: {"merged" if run else "skipped"} contents""")

        # Delete extra READMEs
        for copied_path in copied_paths:
            readme_path = copied_path.joinpath(Files.README)
            if readme_path.exists():
                files.delete(readme_path)

    def compile(self, assignment: CompilationAssignment, context: Context):
        self.output_path.mkdir(exist_ok=True)
        self.compile_readme(assignment, context)
        self.aggregate_contents(assignment, context)


class GradingCompilationUnit(CompilationUnit):
    """Assemble grading scripts and rubric."""

    output_path: Path
    readme_builder: ReadmeBuilder
    content_aggregator: DirectoryAggregator

    def __init__(self, configuration: Configuration):
        super().__init__(configuration)
        self.output_path = self.configuration.artifacts_path.joinpath(Paths.GRADING)
        self.readme_builder = ReadmeBuilder(
            configuration=self.configuration,
            readme_relative_path=Paths.GRADING,
            template_relative_path=Templates.Grading.ASSIGNMENT,
            destination_path=self.output_path)
        self.content_aggregator = DirectoryAggregator(
            contents_relative_path=Paths.GRADING,
            destination_path=self.output_path,
            filter_problems=lambda p: p.grading.automated,
            directory_name=lambda p: p.short)

    def compile_readme(self, assignment: CompilationAssignment, context: Context):
        run, _ = self.readme_builder.run_if_should(assignment, context)
        log.info(f"""solution: {"built" if run else "skipped"} readme""")

    def aggregate_contents(self, assignment: CompilationAssignment, context: Context):
        run, copied_paths = self.content_aggregator.run_if_should(assignment, context)
        log.info(f"""solution: {"merged" if run else "skipped"} contents""")

        # Delete extra READMEs
        for copied_path in copied_paths:
            readme_path = copied_path.joinpath(Files.README)
            if readme_path.exists():
                files.delete(readme_path)

    def dump_index(self, assignment: CompilationAssignment):
        with self.output_path.joinpath(Files.INDEX).open("w") as file:
            json.dump(assignment.dump(), file, indent=2)

    def compile(self, assignment: CompilationAssignment, context: Context):
        self.output_path.mkdir(exist_ok=True)
        self.compile_readme(assignment, context)
        self.aggregate_contents(assignment, context)
        self.dump_index(assignment)


class CurriculaCompilation(Compilation):
    """Repeatable build instructions."""

    custom_template_path: Path
    instructions: InstructionsCompilationUnit
    resources: ResourcesCompilationUnit
    solution: SolutionCompilationUnit
    grading: GradingCompilationUnit

    def __init__(
            self,
            assignment_path: Path,
            artifacts_path: Path,
            custom_template_path: Path = None,
            options: dict = None):
        """Initialize the compilation and do static setup."""

        super().__init__(Configuration(
            assignment_path=assignment_path,
            artifacts_path=artifacts_path,
            options=options))

        self.custom_template_path = custom_template_path
        if self.custom_template_path is not None:
            log.info(f"custom template path is {self.custom_template_path}")

        self.instructions = InstructionsCompilationUnit(self.configuration)
        self.resources = ResourcesCompilationUnit(self.configuration)
        self.solution = SolutionCompilationUnit(self.configuration)
        self.grading = GradingCompilationUnit(self.configuration)

    def compile(self, paths_modified: Optional[Set[Path]] = None):
        """Generate context and compile."""

        log.info(f"building {self.configuration.assignment_path} to {self.configuration.artifacts_path}")

        # Validate first
        validate(self.configuration.assignment_path)

        # Load the assignment object
        log.debug("loading assignment")
        assignment = CompilationAssignment.read(self.configuration.assignment_path)

        # Set up templating
        problem_template_paths = {f"problem/{problem.short}": problem.path for problem in assignment.problems}
        environment = jinja2_create_environment(
            assignment_path=self.configuration.assignment_path,
            problem_paths=problem_template_paths,
            custom_template_path=self.custom_template_path)
        environment.filters.update(get_readme=get_readme, has_readme=has_readme)
        environment.globals["configuration"] = self.configuration

        # Define context
        log.debug("setting context")
        context = Context(environment=environment, paths_modified=paths_modified)

        # Create output directory
        self.configuration.artifacts_path.mkdir(exist_ok=True, parents=True)

        # Run units
        self.instructions.compile(assignment, context)
        self.resources.compile(assignment, context)
        self.solution.compile(assignment, context)
        self.grading.compile(assignment, context)


@timed("compile", printer=log.info)
def compile(assignment_path: Path, artifacts_path: Path, custom_template_path: Path = None, **options):
    """Build the assignment at a given path."""

    CurriculaCompilation(
        assignment_path=assignment_path,
        artifacts_path=artifacts_path,
        custom_template_path=custom_template_path,
        options=options).compile()
