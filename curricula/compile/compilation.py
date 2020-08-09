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

from ..shared import Files, Paths
from ..library.template import jinja2_create_environment
from ..library import files
from ..log import log

from .validate import validate
from .content import ReadmeBuilder, DirectoryMerger, DirectoryAggregator, get_readme, has_readme
from .models import CompilationAssignment
from .framework import Unit, UnitResult, Context, Configuration, Target, TargetResult
from .workflows.grade import GradeWorkflow
from .workflows.site import SiteWorkflow

root = Path(__file__).parent.absolute()


class InstructionsUnit(Unit):
    """Builds the instructions and assets."""

    output_path: Path
    readme_builder: ReadmeBuilder
    asset_merger: DirectoryMerger

    name = "instructions"
    README = "readme"
    ASSETS = "assets"

    def __init__(self, configuration: Configuration):
        """Create builders."""

        super().__init__(configuration)
        self.output_path = self.configuration.artifacts_path.joinpath(Paths.INSTRUCTIONS)

        self.readme_builder = ReadmeBuilder(
            configuration=self.configuration,
            readme_relative_path=Paths.DOT,
            template_relative_path=Paths.INSTRUCTIONS,
            destination_path=self.output_path)
        self.asset_merger = DirectoryMerger(
            contents_relative_path=Paths.ASSETS,
            destination_path=self.output_path.joinpath(Paths.ASSETS))

    def compile_readme(self, assignment: CompilationAssignment, context: Context, result: UnitResult):
        """Combine instructions."""

        run, _ = self.readme_builder.run_if_should(assignment, context)
        log.info(f"""instructions: {"built" if run else "skipped"} readme""")
        if run:
            result.compiled = True
            result.tags.add(self.README)

    def merge_assets(self, assignment: CompilationAssignment, context: Context, result: UnitResult):
        """Combine instruction assets into one folder."""

        run, _ = self.asset_merger.run_if_should(assignment, context)
        log.info(f"""instructions: {"merged" if run else "skipped"} assets""")
        if run:
            result.compiled = True
            result.tags.add(self.ASSETS)

    def compile(self, assignment: CompilationAssignment, context: Context) -> UnitResult:
        """Create directory and add README and assets."""

        result = UnitResult()
        self.output_path.mkdir(exist_ok=True)
        self.compile_readme(assignment, context, result)
        self.merge_assets(assignment, context, result)
        return result


class ResourcesUnit(Unit):
    """Builds the instructions and assets."""

    output_path: Path
    content_aggregator: DirectoryAggregator

    name = "resources"
    RESOURCES = "resources"

    def __init__(self, configuration: Configuration):
        """Only a content aggregator here."""

        super().__init__(configuration)
        self.output_path = self.configuration.artifacts_path.joinpath(Paths.RESOURCES)
        self.content_aggregator = DirectoryAggregator(
            contents_relative_path=Paths.RESOURCES,
            destination_path=self.output_path,
            directory_name=lambda p: p.relative_path)

    def compile(self, assignment: CompilationAssignment, context: Context) -> UnitResult:
        """Bring the problem resources into one directory."""

        result = UnitResult()
        run, _ = self.content_aggregator.run_if_should(assignment, context)
        log.info(f"""resources: {"aggregated" if run else "skipped"} resources""")
        if run:
            result.compiled = True
            result.tags.add(self.RESOURCES)
        return result


class SolutionUnit(Unit):
    """Creates cheat sheet and solution code."""

    output_path: Path
    readme_builder: ReadmeBuilder
    content_aggregator: DirectoryAggregator

    name = "solution"
    README = "readme"
    CONTENTS = "contents"

    def __init__(self, configuration: Configuration):
        """Configure and setup builders."""

        super().__init__(configuration)
        self.output_path = self.configuration.artifacts_path.joinpath(Paths.SOLUTION)

        self.readme_builder = ReadmeBuilder(
            configuration=self.configuration,
            readme_relative_path=Paths.SOLUTION,
            template_relative_path=Paths.SOLUTION,
            destination_path=self.output_path)
        self.content_aggregator = DirectoryAggregator(
            contents_relative_path=Paths.SOLUTION,
            destination_path=self.output_path,
            directory_name=lambda p: p.relative_path)

    def compile_readme(self, assignment: CompilationAssignment, context: Context, result: UnitResult):
        """Assemble cheat sheet."""

        run, _ = self.readme_builder.run_if_should(assignment, context)
        log.info(f"""solution: {"built" if run else "skipped"} readme""")
        if run:
            result.compiled = True
            result.tags.add(self.README)

    def aggregate_contents(self, assignment: CompilationAssignment, context: Context, result: UnitResult):
        """Match resources with solutions."""

        run, copied_paths = self.content_aggregator.run_if_should(assignment, context)
        log.info(f"""solution: {"merged" if run else "skipped"} contents""")

        if run:
            # Delete extra READMEs
            for copied_path in copied_paths:
                readme_path = copied_path.joinpath(Files.README)
                if readme_path.exists():
                    files.delete(readme_path)

            result.compiled = True
            result.tags.add(self.CONTENTS)

    def compile(self, assignment: CompilationAssignment, context: Context) -> UnitResult:
        """Run and get result."""

        result = UnitResult()
        self.output_path.mkdir(exist_ok=True)
        self.compile_readme(assignment, context, result)
        self.aggregate_contents(assignment, context, result)
        return result


class GradingUnit(Unit):
    """Assemble grading scripts and rubric."""

    output_path: Path
    readme_builder: ReadmeBuilder
    content_aggregator: DirectoryAggregator

    name = "grading"
    README = "readme"
    CONTENTS = "contents"
    INDEX = "index"

    def __init__(self, configuration: Configuration):
        """Configure and setup builders."""

        super().__init__(configuration)
        self.output_path = self.configuration.artifacts_path.joinpath(Paths.GRADING)

        self.readme_builder = ReadmeBuilder(
            configuration=self.configuration,
            readme_relative_path=Paths.GRADING,
            template_relative_path=Paths.GRADING,
            destination_path=self.output_path)
        self.content_aggregator = DirectoryAggregator(
            contents_relative_path=Paths.GRADING,
            destination_path=self.output_path,
            filter_problems=lambda p: p.grading.automated,
            directory_name=lambda p: p.short)

    def compile_readme(self, assignment: CompilationAssignment, context: Context, result: UnitResult):
        """Assemble rubric."""

        run, _ = self.readme_builder.run_if_should(assignment, context)
        log.info(f"""solution: {"built" if run else "skipped"} readme""")

        if run:
            result.compiled = True
            result.tags.add(self.README)

    def aggregate_contents(self, assignment: CompilationAssignment, context: Context, result: UnitResult):
        """Get all grading scripts."""

        run, copied_paths = self.content_aggregator.run_if_should(assignment, context)
        log.info(f"""solution: {"merged" if run else "skipped"} contents""")

        if run:
            # Delete extra READMEs
            for copied_path in copied_paths:
                readme_path = copied_path.joinpath(Files.README)
                if readme_path.exists():
                    files.delete(readme_path)

            result.compiled = True
            result.tags.add(self.CONTENTS)

    def dump_index(self, assignment: CompilationAssignment, result: UnitResult):
        """Dump the assignment for grading reference."""

        with self.output_path.joinpath(Files.INDEX).open("w") as file:
            json.dump(assignment.dump(), file, indent=2)
        result.compiled = True
        result.tags.add(self.INDEX)

    def compile(self, assignment: CompilationAssignment, context: Context):
        """Compile rubric, grading scripts, and index."""

        result = UnitResult()
        self.output_path.mkdir(exist_ok=True)
        self.compile_readme(assignment, context, result)
        self.aggregate_contents(assignment, context, result)
        self.dump_index(assignment, result)
        return result


class CurriculaTarget(Target):
    """Repeatable build instructions."""

    configuration: Configuration

    def __init__(self, configuration: Configuration):
        """Initialize the compilation and do static setup."""

        super().__init__(configuration)

        # Register compilation units
        self.unit(InstructionsUnit)
        self.unit(ResourcesUnit)
        self.unit(SolutionUnit)
        self.unit(GradingUnit)

        # Register additional workflows
        self.workflow(GradeWorkflow)
        self.workflow(SiteWorkflow)

    def compile(self, **context_options) -> TargetResult:
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
            custom_template_path=self.configuration.custom_template_path)
        environment.filters.update(get_readme=get_readme, has_readme=has_readme)
        environment.globals["configuration"] = self.configuration

        # Define context
        log.debug("setting context")
        context = Context(environment=environment, **context_options)

        # Check if an index file was edited
        if context.paths_modified:
            for item in (assignment, *assignment.problems):
                if item.index_path.resolve() in context.paths_modified:
                    context.indices_modified = True
                    break

        # Create output directory
        self.configuration.artifacts_path.mkdir(exist_ok=True, parents=True)

        # Run units
        return super().compile(assignment, context)
