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

import jinja2
import json
from pathlib import Path
from typing import Dict, Union, List, Callable
from dataclasses import dataclass

from .validate import validate
from .models import CompilationProblem, CompilationAssignment

from ..shared import Files, Paths
from ..library.template import jinja2_create_environment
from ..library import files
from ..library.utility import timed
from ..log import log


root = Path(__file__).parent.absolute()


@dataclass(repr=False, eq=False)
class Context:
    """Build context.

    The build context is simply a container for information about the
    build that's passed to each step.
    """

    environment: jinja2.Environment
    assignment_path: Path
    artifacts_path: Path
    options: Dict[str, str]


def compile_readme(
        context: Context,
        assignment: CompilationAssignment,
        template_relative_path: str,
        destination_path: Path) -> Path:
    """Compile a README from an assignment.

    This function returns the final path of the README, which may be
    different if the provided destination is a directory.
    """

    log.debug(f"compiling readme for {destination_path}")
    template = context.environment.get_template(f"template:compile/{template_relative_path}")
    if destination_path.is_dir():
        destination_path = destination_path.joinpath(Files.README)
    with destination_path.open("w") as file:
        file.write(template.render(assignment=assignment))
    return destination_path


def merge_contents(
        context: Context,
        assignment: CompilationAssignment,
        contents_relative_path: Path,
        destination_path: Path,
        filter_problems: Callable[[CompilationProblem], bool] = None):
    """Compile subdirectories from problems into a single directory."""

    log.debug(f"merging contents to {destination_path}")

    destination_path.mkdir(exist_ok=True)

    # First copy any assignment-wide resources
    assignment_contents_path = context.assignment_path.joinpath(contents_relative_path)
    if assignment_contents_path.exists():
        files.copy_directory(assignment_contents_path, destination_path)

    # Overwrite with problem contents, enable filtration
    for problem in filter(filter_problems, assignment.problems):
        problem_contents_path = problem.relative_path.joinpath(contents_relative_path)
        if problem_contents_path.exists():
            files.copy_directory(problem_contents_path, destination_path, merge=True)


def aggregate_contents(
        assignment: CompilationAssignment,
        contents_relative_path: Path,
        destination_path: Path,
        filter_problems: Callable[[CompilationProblem], bool] = None,
        rename: Callable[[CompilationProblem], str] = None) -> List[Path]:
    """Compile subdirectories from problems to respective directories.

    Different from merge in that the result is a directory of
    directories. Returns a list of the resultant folders that were
    copied into the destination.
    """

    log.debug(f"aggregating contents to {destination_path}")

    destination_path.mkdir(exist_ok=True)

    # First compile assignment-wide assets
    assignment_contents_path = assignment.path.joinpath(contents_relative_path)
    if assignment_contents_path.exists():
        files.copy_directory(assignment_contents_path, destination_path)

    # Copy per problem, enable filtration
    copied_paths = []
    for problem in filter(filter_problems, assignment.problems):
        problem_contents_path = problem.path.joinpath(contents_relative_path)
        if problem_contents_path.exists():
            problem_destination_path = destination_path.joinpath(problem.short if rename is None else rename(problem))
            copied_paths.append(problem_destination_path)
            files.copy_directory(problem_contents_path, problem_destination_path)

    return copied_paths


def build_instructions(context: Context, assignment: CompilationAssignment) -> Path:
    """Compile instruction readme and assets."""

    log.debug("compiling instructions")
    instructions_path = context.artifacts_path.joinpath(Paths.INSTRUCTIONS)
    instructions_path.mkdir(exist_ok=True)
    compile_readme(context, assignment, "instructions/assignment.md", instructions_path)
    merge_contents(context, assignment, Paths.ASSETS, instructions_path.joinpath(Paths.ASSETS))
    return instructions_path


def build_resources(context: Context, assignment: CompilationAssignment) -> Path:
    """Compile resources files."""

    log.debug("compiling resources")
    resources_path = context.artifacts_path.joinpath(Paths.RESOURCES)
    resources_path.mkdir(exist_ok=True)
    aggregate_contents(
        assignment=assignment,
        contents_relative_path=Paths.RESOURCES,
        destination_path=resources_path,
        rename=lambda p: p.relative_path)
    return resources_path


def build_solution_readme(context: Context, assignment: CompilationAssignment, path: Path):
    """Generate the composite cheat sheet README."""

    log.debug("building cheat sheet")
    assignment_template = context.environment.get_template("template:compile/solution/assignment.md")
    with path.joinpath(Files.README).open("w") as file:
        file.write(assignment_template.render(assignment=assignment))


def build_solution_code(assignment: CompilationAssignment, path: Path):
    """Compile only submission files of the solution."""

    log.debug("assembling solution code")
    copied_paths = aggregate_contents(
        assignment=assignment,
        contents_relative_path=Paths.SOLUTION,
        destination_path=path,
        rename=lambda p: p.relative_path)

    # Delete extra READMEs
    for copied_path in copied_paths:
        readme_path = copied_path.joinpath(Files.README)
        if readme_path.exists():
            files.delete(readme_path)


def build_solution(context: Context, assignment: CompilationAssignment) -> Path:
    """Compile cheatsheets."""

    log.debug("compiling solution")
    solution_path = context.artifacts_path.joinpath(Paths.SOLUTION)
    solution_path.mkdir(exist_ok=True)
    build_solution_readme(context, assignment, solution_path)
    build_solution_code(assignment, solution_path)
    return solution_path


def build_grading_readme(context: Context, assignment: CompilationAssignment, path: Path):
    """Aggregate README for rubric."""

    log.debug("building grading instructions")
    assignment_template = context.environment.get_template("template:compile/grading/assignment.md")
    with path.joinpath(Files.README).open("w") as file:
        file.write(assignment_template.render(assignment=assignment))


def build_grading(context: Context, assignment: CompilationAssignment) -> Path:
    """Compile rubrics."""

    log.debug("compiling grading")

    grading_path = context.artifacts_path.joinpath(Paths.GRADING)
    grading_path.mkdir(exist_ok=True)
    build_grading_readme(context, assignment, grading_path)
    copied_paths = aggregate_contents(
        assignment,
        Paths.GRADING,
        grading_path,
        filter_problems=lambda p: p.grading.automated)

    # Delete extra READMEs
    for copied_path in copied_paths:
        readme_path = copied_path.joinpath(Files.README)
        if readme_path.exists():
            files.delete(readme_path)

    with grading_path.joinpath(Files.INDEX).open("w") as file:
        json.dump(assignment.dump(), file, indent=2)

    return grading_path


@jinja2.environmentfilter
def get_readme(
        environment: jinja2.Environment,
        item: Union[CompilationProblem, CompilationAssignment],
        *component: str) -> str:
    """Render a README with options for nested path."""

    readme_path = "/".join(component + (Files.README,))

    try:
        if isinstance(item, CompilationAssignment):
            return environment \
                .get_template(f"assignment:{readme_path}") \
                .render(assignment=item)
        elif isinstance(item, CompilationProblem):
            return environment \
                .get_template(f"problem/{item.short}:{readme_path}") \
                .render(assignment=item.assignment, problem=item)

    except jinja2.exceptions.TemplateNotFound as exception:
        log.error(f"error finding {exception}")
        return ""


def has_readme(item: Union[CompilationProblem, CompilationAssignment], *component: str) -> bool:
    """Check whether a problem has a solution README."""

    return item.path.joinpath(*component, Files.README).exists()


BUILD_STEPS = (
    build_instructions,
    build_resources,
    build_solution,
    build_grading)


@timed("compile", printer=log.info)
def compile(assignment_path: Path, artifacts_path: Path, template_path: Path = None, **options):
    """Build the assignment at a given path."""

    log.info(f"building {assignment_path} to {artifacts_path}")

    if template_path is not None:
        log.info(f"custom template path is {template_path}")

    # Validate first
    validate(assignment_path)

    # Load the assignment object
    log.debug("loading assignment")
    assignment = CompilationAssignment.read(assignment_path)

    # Set up templating
    problem_template_paths = {f"problem/{problem.short}": problem.path for problem in assignment.problems}
    environment = jinja2_create_environment(
        assignment_path=assignment_path,
        problem_paths=problem_template_paths,
        custom_template_path=template_path)
    environment.filters.update(get_readme=get_readme, has_readme=has_readme)

    # Define context
    log.debug("setting context")
    context = Context(environment, assignment_path, artifacts_path, options)
    environment.globals["context"] = context

    # Create output directory
    artifacts_path.mkdir(exist_ok=True, parents=True)

    # Build
    for step in BUILD_STEPS:
        step(context, assignment)
