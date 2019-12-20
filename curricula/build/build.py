import jinja2
import json
from pathlib import Path
from typing import Dict, Union, List, Callable
from dataclasses import dataclass

from ..core.models import Assignment, Problem
from ..core.shared import Files, Paths
from ..grade.manager import generate_grading_schema
from ..library.template import jinja2_create_environment
from ..library import files
from ..library.utility import timed

root = Path(__file__).absolute().parent


@dataclass(repr=False, eq=False)
class Context:
    """Build context."""

    environment: jinja2.Environment
    assignment_path: Path
    artifacts_path: Path
    options: Dict[str, str]


def compile_readme(
        context: Context,
        assignment: Assignment,
        template_relative_path: str,
        destination_path: Path) -> Path:
    """Compile a README from an assignment.

    This function returns the final path of the README, which may be
    different if the provided destination is a directory.
    """

    template = context.environment.get_template(f"template/{template_relative_path}")
    if destination_path.is_dir():
        destination_path = destination_path.joinpath(Files.README)
    with destination_path.open("w") as file:
        file.write(template.render(assignment=assignment))
    return destination_path


def merge_contents(
        assignment: Assignment,
        contents_relative_path: Path,
        destination_path: Path,
        filter_problems: Callable[[Problem], bool] = None):
    """Compile subdirectories from problems into a single directory."""

    destination_path.mkdir(exist_ok=True)

    # First copy any assignment-wide resources
    assignment_contents_path = assignment.path.joinpath(contents_relative_path)
    if assignment_contents_path.exists():
        files.copy_directory(assignment_contents_path, destination_path)

    # Overwrite with problem contents, enable filtration
    for problem in filter(filter_problems, assignment.problems):
        problem_contents_path = problem.path.joinpath(contents_relative_path)
        if problem_contents_path.exists():
            files.copy_directory(problem_contents_path, destination_path, merge=True)


def aggregate_contents(
        assignment: Assignment,
        contents_relative_path: Path,
        destination_path: Path,
        filter_problems: Callable[[Problem], bool] = None) -> List[Path]:
    """Compile subdirectories from problems to respective directories.

    This method returns a list of the resultant folders that were
    copied into the destination.
    """

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
            problem_destination_path = destination_path.joinpath(problem.short)
            copied_paths.append(problem_destination_path)
            files.copy_directory(problem_contents_path, problem_destination_path)

    return copied_paths


def build_instructions(context: Context, assignment: Assignment):
    """Build all site components."""

    instructions_path = context.artifacts_path.joinpath(Paths.INSTRUCTIONS)
    instructions_path.mkdir(exist_ok=True)
    compile_readme(context, assignment, "instructions/assignment.md", instructions_path)
    merge_contents(assignment, Paths.ASSETS, instructions_path.joinpath(Paths.ASSETS))


def build_resources(context: Context, assignment: Assignment):
    """Compile resources files."""

    resources_path = context.artifacts_path.joinpath(Paths.RESOURCES)
    resources_path.mkdir(exist_ok=True)
    aggregate_contents(assignment, Paths.RESOURCES, resources_path)


def build_solution_readme(context: Context, assignment: Assignment, path: Path):
    """Generate the composite README."""

    assignment_template = context.environment.get_template("template/solution/assignment.md")
    with path.joinpath(Files.README).open("w") as file:
        file.write(assignment_template.render(assignment=assignment))


def build_solution_code(assignment: Assignment, path: Path):
    """Compile only submission files of the solution."""

    for problem in assignment.problems:
        problem_solution_path = problem.path.joinpath(Paths.SOLUTION)
        if problem_solution_path.exists() and problem.submission:
            for submission_path in map(Path, problem.submission):
                relative_source_path = problem.path.joinpath(Paths.SOLUTION, *submission_path.parts[1:])
                relative_destination_path = path.joinpath(problem.short, *submission_path.parts[1:])
                relative_destination_path.parent.mkdir(parents=True, exist_ok=True)
                files.copy(relative_source_path, relative_destination_path)


def build_solution(context: Context, assignment: Assignment):
    """Compile cheatsheets."""

    solution_path = context.artifacts_path.joinpath(Paths.SOLUTION)
    solution_path.mkdir(exist_ok=True)
    build_solution_readme(context, assignment, solution_path)
    build_solution_code(assignment, solution_path)


def build_grading_readme(context: Context, assignment: Assignment, path: Path):
    """Aggregate README for rubric."""

    assignment_template = context.environment.get_template("template/grading/assignment.md")
    with path.joinpath(Files.README).open("w") as file:
        file.write(assignment_template.render(assignment=assignment))


def build_grading_schema(assignment: Assignment, path: Path):
    """Generate a JSON data file with grading metadata."""

    with path.joinpath(Files.GRADING).open("w") as file:
        json.dump(generate_grading_schema(path, assignment), file, indent=2)


def build_grading(context: Context, assignment: Assignment):
    """Compile rubrics."""

    grading_path = context.artifacts_path.joinpath(Paths.GRADING)
    grading_path.mkdir(exist_ok=True)
    build_grading_readme(context, assignment, grading_path)
    copied_paths = aggregate_contents(
        assignment,
        Paths.GRADING,
        grading_path,
        filter_problems=lambda p: "automated" in p.grading.process)

    # Delete extra READMEs
    for copied_path in copied_paths:
        readme_path = copied_path.joinpath(Files.README)
        if readme_path.exists():
            files.delete(readme_path)

    build_grading_schema(assignment, grading_path)


BUILD_STEPS = (
    build_instructions,
    build_resources,
    build_solution,
    build_grading
)


@jinja2.environmentfilter
def get_readme(environment: jinja2.Environment, item: Union[Problem, Assignment], *component: str) -> str:
    """Render a README with options for nested path."""

    context: Context = environment.globals["context"]  # Not jinja2 context, our context
    readme_path = item.path.joinpath(*component, Files.README).relative_to(context.assignment_path)

    if isinstance(item, Assignment):
        return environment.get_template(str(readme_path)).render(assignment=item)
    elif isinstance(item, Problem):
        return environment.get_template(str(readme_path)).render(assignment=item.assignment, problem=item)


def has_readme(item: Union[Problem, Assignment], *component: str) -> bool:
    """Check whether a problem has a solution README."""

    return item.path.joinpath(*component, Files.README).exists()


@timed("Build")
def build(assignment_path: Path, artifacts_path: Path, **options):
    """Build the assignment at a given path."""

    if not assignment_path.is_dir():
        raise ValueError("assignment path does not exist!")

    environment = jinja2_create_environment(assignment_path, root)
    environment.filters.update(get_readme=get_readme, has_readme=has_readme)
    context = Context(environment, assignment_path, artifacts_path, options)
    environment.globals["context"] = context

    artifacts_path.mkdir(exist_ok=True, parents=True)

    assignment = Assignment.load(assignment_path)
    files.replace_directory(artifacts_path)

    for step in BUILD_STEPS:
        step(context, assignment)
