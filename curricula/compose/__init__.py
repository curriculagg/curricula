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
from dataclasses import dataclass, field

from .validate import validate

from ..models import Assignment, Problem
from ..shared import Files, Paths
from ..library.template import jinja2_create_environment
from ..library import files
from ..library.utility import timed
from ..log import log

from ..grade.manager import import_grader


class BuildProblem(Problem):
    """Add additional fields only used for build."""

    number: int
    path: Path
    assignment: "BuildAssignment"

    @classmethod
    def read(cls, assignment: "BuildAssignment", reference: dict, root: Path, number: int) -> "BuildProblem":
        """Load a problem from the assignment path and reference."""

        path = root.joinpath(reference["path"])
        with path.joinpath(Files.PROBLEM).open() as file:
            data = json.load(file)

        data["short"] = reference.get("short", data.get("short", path.parts[-1]))
        data["relative_path"] = reference.get("relative_path", path.parts[-1])

        if "title" in reference:
            data["title"] = reference["title"]

        data["grading"]["enabled"] = reference["grading"].get("enabled", True)
        data["grading"]["weight"] = reference["grading"].get("weight", "1")
        data["grading"]["points"] = reference["grading"].get("points", "100")
        for category in "automated", "review", "manual":
            category_data = data["grading"][category]
            if category_data is None:
                continue

            if category in reference["grading"]:
                reference_category_data = reference["grading"][category]

                if "enabled" in reference_category_data:
                    category_data["enabled"] = reference_category_data
                if "weight" in reference_category_data:
                    category_data["weight"] = reference_category_data["weight"]
                if "points" in reference_category_data:
                    category_data["points"] = reference_category_data["points"]

            if "weight" not in category_data:
                category_data["weight"] = "1"
            if "points" not in category_data:
                category_data["points"] = "100"

        self = cls.load(data)

        # Convenience details for rendering
        self.assignment = assignment
        self.number = number
        self.path = path

        return self


class BuildAssignment(Assignment):
    """Additional fields for build."""

    problems: List[BuildProblem]
    path: Path = field(init=False)

    @classmethod
    def read(cls, path: Path) -> "BuildAssignment":
        """Load an assignment from a containing directory."""

        with path.joinpath(Files.ASSIGNMENT).open() as file:
            data = json.load(file)

        data["short"] = data.get("short", path.parts[-1])
        self = cls.load(data, problems=[])

        counter = 1
        for reference in data.pop("problems"):
            number = None
            if any(filter(None, reference["grading"])):
                number = counter
                counter += 1

            problem = BuildProblem.read(self, reference, path, number)
            self.problems.append(problem)

        self.path = path

        return self


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
        assignment: BuildAssignment,
        template_relative_path: str,
        destination_path: Path) -> Path:
    """Compile a README from an assignment.

    This function returns the final path of the README, which may be
    different if the provided destination is a directory.
    """

    log.debug(f"compiling readme for {destination_path}")
    template = context.environment.get_template(f"template:build/{template_relative_path}")
    if destination_path.is_dir():
        destination_path = destination_path.joinpath(Files.README)
    with destination_path.open("w") as file:
        file.write(template.render(assignment=assignment))
    return destination_path


def merge_contents(
        context: Context,
        assignment: BuildAssignment,
        contents_relative_path: Path,
        destination_path: Path,
        filter_problems: Callable[[BuildProblem], bool] = None):
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
        assignment: BuildAssignment,
        contents_relative_path: Path,
        destination_path: Path,
        filter_problems: Callable[[BuildProblem], bool] = None,
        rename: Callable[[BuildProblem], str] = None) -> List[Path]:
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


def build_instructions(context: Context, assignment: BuildAssignment):
    """Compile instruction readme and assets."""

    log.debug("compiling instructions")
    instructions_path = context.artifacts_path.joinpath(Paths.INSTRUCTIONS)
    instructions_path.mkdir(exist_ok=True)
    compile_readme(context, assignment, "instructions/assignment.md", instructions_path)
    merge_contents(context, assignment, Paths.ASSETS, instructions_path.joinpath(Paths.ASSETS))


def build_resources(context: Context, assignment: BuildAssignment):
    """Compile resources files."""

    log.debug("compiling resources")
    resources_path = context.artifacts_path.joinpath(Paths.RESOURCES)
    resources_path.mkdir(exist_ok=True)
    aggregate_contents(assignment, Paths.RESOURCES, resources_path, rename=lambda p: p.directory)


def build_solution_readme(context: Context, assignment: Assignment, path: Path):
    """Generate the composite cheat sheet README."""

    log.debug("building cheat sheet")
    assignment_template = context.environment.get_template("template:build/solution/assignment.md")
    with path.joinpath(Files.README).open("w") as file:
        file.write(assignment_template.render(assignment=assignment))


def build_solution_code(assignment: BuildAssignment, path: Path):
    """Compile only submission files of the solution."""

    log.debug("assembling solution code")
    copied_paths = aggregate_contents(assignment, Paths.SOLUTION, path, rename=lambda p: p.directory)

    # Delete extra READMEs
    for copied_path in copied_paths:
        readme_path = copied_path.joinpath(Files.README)
        if readme_path.exists():
            files.delete(readme_path)


def build_solution(context: Context, assignment: BuildAssignment):
    """Compile cheatsheets."""

    log.debug("compiling solution")
    solution_path = context.artifacts_path.joinpath(Paths.SOLUTION)
    solution_path.mkdir(exist_ok=True)
    build_solution_readme(context, assignment, solution_path)
    build_solution_code(assignment, solution_path)


def build_grading_readme(context: Context, assignment: Assignment, path: Path):
    """Aggregate README for rubric."""

    log.debug("building grading instructions")
    assignment_template = context.environment.get_template("template:build/grading/assignment.md")
    with path.joinpath(Files.README).open("w") as file:
        file.write(assignment_template.render(assignment=assignment))


def generate_grading_schema(grading_path: Path, assignment: Assignment) -> dict:
    """Generate a JSON schema describing the grading package.

    This method requires the grading artifact to already have been
    aggregated, as it has to access the individual problem graders to
    dump their task summaries.
    """

    assignment_schema = dict(title=assignment.title, short=assignment.short, problems=dict())
    for problem in assignment.problems:
        if problem.grading.automated:
            grader = import_grader(grading_path.joinpath(problem.short, Files.TESTS))
            assignment_schema["problems"][problem.short] = dict(
                title=problem.title,
                target_path=str(problem.relative_path),
                tasks=grader.dump())
    return assignment_schema


def build_grading_schema(assignment: Assignment, path: Path):
    """Generate a JSON data file with grading metadata."""

    log.debug("building grading schema")
    with path.joinpath(Files.GRADING).open("w") as file:
        json.dump(generate_grading_schema(path, assignment), file, indent=2)


def build_grading(context: Context, assignment: BuildAssignment):
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

    build_grading_schema(assignment, grading_path)


def build_index(context: Context, assignment: Assignment):
    """Dump the assignment into the artifacts."""

    log.debug("writing index to artifacts")
    with context.artifacts_path.joinpath("index.json").open("w") as file:
        json.dump(assignment.dump(), file, indent=2)


@jinja2.environmentfilter
def get_readme(environment: jinja2.Environment, item: Union[BuildProblem, BuildAssignment], *component: str) -> str:
    """Render a README with options for nested path."""

    readme_path = "/".join(component + (Files.README,))

    try:
        if isinstance(item, BuildAssignment):
            return environment \
                .get_template(f"assignment:{readme_path}") \
                .render(assignment=item)
        elif isinstance(item, BuildProblem):
            return environment \
                .get_template(f"problem/{item.short}:{readme_path}") \
                .render(assignment=item.assignment, problem=item)

    except jinja2.exceptions.TemplateNotFound as exception:
        log.error(f"error finding {exception}")
        return ""


def has_readme(item: Union[Problem, Assignment], *component: str) -> bool:
    """Check whether a problem has a solution README."""

    return item.relative_path.joinpath(*component, Files.README).exists()


BUILD_STEPS = (
    build_instructions,
    build_resources,
    build_solution,
    build_grading,
    build_index)


@timed("build", printer=log.info)
def build(template_path: Path, assignment_path: Path, artifacts_path: Path, **options):
    """Build the assignment at a given path."""

    log.info(f"building {assignment_path} to {artifacts_path}")

    # Validate first
    validate(assignment_path)

    # Load the assignment object
    log.debug("loading assignment")
    assignment = BuildAssignment.read(assignment_path)

    # Set up templating
    problem_template_paths = {f"problem/{problem.short}": problem.path for problem in assignment.problems}
    environment = jinja2_create_environment(
        template=template_path,
        assignment=assignment_path,
        **problem_template_paths)
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
