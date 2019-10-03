import jinja2
from pathlib import Path
from typing import Dict, Union
from dataclasses import dataclass

from ..configurable import jinja2_create_environment
from ..mapping.models import Assignment, Problem
from ..mapping.shared import Files, Paths
from ..library import files
from ..library import markdown


@dataclass(repr=False, eq=False)
class Context:
    """Build context."""

    environment: jinja2.Environment
    material_path: Path
    args: Dict[str, str]


def build_instructions_readme(context: Context, assignment: Assignment, path: Path):
    """Generate the composite README."""

    assignment_template = context.environment.get_template("template/instructions/assignment.md")
    with path.joinpath(Files.README).open("w") as file:
        file.write(assignment_template.render(assignment=assignment))


def build_instructions_assets(assignment: Assignment, path: Path):
    """Compile assets into single folder."""

    # Get setup destination assets
    assets_path = path.joinpath(Paths.ASSETS)
    assets_path.mkdir(exist_ok=True)

    # Copy assignment assets first
    assignment_assets_path = assignment.path.joinpath(Paths.ASSETS)
    if assignment_assets_path.exists():
        files.copy_directory(assignment_assets_path, assets_path)

    # Overwrite by problem
    for problem in assignment.problems:
        problem_assets_path = problem.path.joinpath(Paths.ASSETS)
        if problem_assets_path.exists():
            files.copy_directory(problem_assets_path, assets_path, merge=False)


def build_instructions(context: Context, assignment: Assignment, path: Path):
    """Build all site components."""

    instructions_path = path.joinpath(Paths.INSTRUCTIONS)
    instructions_path.mkdir(exist_ok=True)
    build_instructions_readme(context, assignment, instructions_path)
    build_instructions_assets(assignment, instructions_path)


def build_resources(context: Context, assignment: Assignment, path: Path):
    """Compile resources files."""

    resources_path = path.joinpath(Paths.RESOURCES)
    resources_path.mkdir(exist_ok=True)

    for problem in assignment.problems:

        # Copy over resources
        base_name = problem.path.parts[-1]
        problem_resources_path = problem.path.joinpath(Paths.RESOURCES)
        if problem_resources_path.exists():
            files.copy_directory(problem_resources_path, resources_path.joinpath(base_name))

        # Make sure files required for submission also exist
        if problem.submission:
            for submission_fragment in problem.submission:
                submission_path = resources_path.joinpath(submission_fragment)
                if "." in submission_path.parts[-1] and not submission_path.exists():
                    submission_path.parent.mkdir(parents=True, exist_ok=True)
                    submission_path.touch(exist_ok=True)


def build_solution_readme(context: Context, assignment: Assignment, path: Path):
    """Generate the composite README."""

    assignment_template = context.environment.get_template("template/solution/assignment.md")
    with path.joinpath(Files.README).open("w") as file:
        file.write(assignment_template.render(assignment=assignment))


def build_solution_code(assignment: Assignment, path: Path):
    """Compile only submission files of the solution."""

    solution_path = path.joinpath(Paths.SOLUTION)
    solution_path.mkdir(exist_ok=True)

    for problem in assignment.problems:
        problem_solution_path = problem.path.joinpath(Paths.SOLUTION)
        if problem_solution_path.exists() and problem.submission:
            for submission_path in map(Path, problem.submission):
                relative_source_path = problem.path.joinpath(Paths.SOLUTION, *submission_path.parts[1:])
                relative_destination_path = solution_path.joinpath(problem.short, *submission_path.parts[1:])
                relative_destination_path.parent.mkdir(parents=True, exist_ok=True)
                files.copy(relative_source_path, relative_destination_path)


def build_solution(context: Context, assignment: Assignment, path: Path):
    """Compile cheatsheets."""

    solution_path = path.joinpath(Paths.SOLUTION)
    solution_path.mkdir(exist_ok=True)
    build_solution_readme(context, assignment, solution_path)
    build_solution_code(assignment, solution_path)


def build_grading(context: Context, assignment: Assignment, path: Path):
    """Compile rubrics."""

    grading_path = path.joinpath(Paths.GRADING)
    grading_path.mkdir(exist_ok=True)
    assignment_template = context.environment.get_template("template/grading/assignment.md")
    with grading_path.joinpath(Files.README).open("w") as file:
        file.write(assignment_template.render(assignment=assignment))


BUILD_STEPS = (
    build_instructions,
    build_resources,
    build_grading
)


@jinja2.environmentfilter
def get_readme(environment: jinja2.Environment, item: Union[Problem, Assignment], *component: str) -> str:
    """Render a README with options for nested path."""

    context: Context = environment.globals["context"]  # Not jinja2 context, our context
    readme_path = item.path.joinpath(*component, Files.README).relative_to(context.material_path)

    if isinstance(item, Assignment):
        return environment.get_template(str(readme_path)).render(assignment=item)
    elif isinstance(item, Problem):
        return environment.get_template(str(readme_path)).render(assignment=item.assignment, problem=item)


def has_readme(item: Union[Problem, Assignment], *component: str) -> bool:
    """Check whether a problem has a solution README."""

    return item.path.joinpath(*component, "README.md").exists()


def jinja2_create_build_environment(**options) -> jinja2.Environment:
    """Add a couple filters for content building."""

    environment = jinja2_create_environment(**options)
    environment.filters.update(get_readme=get_readme, has_readme=has_readme)
    return environment


def build(args: dict):
    """Build the assignment at a given path."""

    path = Path(args.pop("material")).absolute()
    environment = jinja2_create_build_environment(loader=jinja2.FileSystemLoader(str(path)))
    context = Context(environment, path, args)
    environment.globals["context"] = context

    artifacts_path = path.parent.joinpath("artifacts")
    artifacts_path.mkdir(exist_ok=True)

    assignment = Assignment.load(path.joinpath("assignment", "hw1"))
    for step in BUILD_STEPS:
        step(context, assignment, artifacts_path)
