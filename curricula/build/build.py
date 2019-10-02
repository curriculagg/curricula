import jinja2
from pathlib import Path
from typing import Any, Dict
from dataclasses import dataclass

from ..configurable import create_jinja2_environment
from ..mapping.models import Assignment, Problem
from ..mapping.shared import Files, Paths
from ..library import files
from ..library import markdown


@dataclass(repr=False, eq=False)
class Context:
    """Build context."""

    environment: jinja2.Environment
    path: Path
    args: Dict[str, str]


def load_markdown(path: Path, **namespace: Any) -> str:
    """Load a markdown file and interpolate."""

    if not path.is_file():
        path = path.joinpath("README.md")
    with path.open() as file:
        return markdown.Loader.load(file, **namespace)


def build_instructions_readme(context: Context, assignment: Assignment, path: Path):
    """Generate the composite README."""

    assignment_template = context.environment.get_template("template/instructions/assignment.md")
    problem_template = context.environment.get_template("template/instructions/problem.md")
    problems = []

    for problem in assignment.problems:
        readme_path = files.relative(context.path, problem.path.joinpath("README.md"))
        instructions = context.environment.get_template(str(readme_path)).render(
            assignment=assignment,
            problem=problem)
        problems.append(problem_template.render(
            assignment=assignment,
            problem=problem,
            instructions=instructions).strip())

    with path.joinpath("README.md").open("w") as file:
        readme_path = files.relative(context.path, assignment.path.joinpath("README.md"))
        instructions = context.environment.get_template(str(readme_path)).render(
            assignment=assignment)
        file.write(assignment_template.render(
            assignment=assignment,
            instructions=instructions,
            problems="\n\n".join(problems)))


def build_assets(assignment: Assignment, path: Path):
    """Compile assets into single folder."""

    # Get setup destination assets
    assets_path = path.joinpath("assets")
    assets_path.mkdir()

    # Copy assignment assets first
    assignment_assets_path = assignment.path.joinpath("assets")
    if assignment_assets_path.exists():
        files.copy_directory(assignment_assets_path, assets_path)

    # Overwrite by problem
    for problem in assignment.problems:
        problem_assets_path = problem.path.joinpath("assets")
        if problem_assets_path.exists():
            files.copy_directory(problem_assets_path, assets_path, merge=False)


def build_instructions(context: Context, assignment: Assignment, path: Path):
    """Build all site components."""

    instructions_path = path.joinpath(Paths.INSTRUCTIONS)
    instructions_path.mkdir(exist_ok=True)
    build_instructions_readme(context, assignment, instructions_path)
    #build_assets(assignment, site_path)


def build_skeleton(assignment: Assignment, path: Path):
    """Compile skeleton files."""

    skeleton_path = path.joinpath(Paths.SKELETON)
    skeleton_path.mkdir()

    for problem in assignment.problems:
        base_name = problem.path.parts[-1]
        problem_skeleton_path = problem.path.joinpath(Paths.SKELETON)
        if problem_skeleton_path.exists():
            files.copy_directory(problem_skeleton_path, skeleton_path.joinpath(base_name))

        if problem.submission:
            for submission_fragment in problem.submission:
                submission_path = skeleton_path.joinpath(submission_fragment)
                if "." in submission_path.parts[-1] and not submission_path.exists():
                    submission_path.parent.mkdir(parents=True, exist_ok=True)
                    submission_path.touch(exist_ok=True)


def build_cheatsheet(assignment: Assignment, path: Path):
    """Generate the composite README."""

    with path.joinpath(Files.README).open("w") as readme:
        readme.write(markdown.header(assignment.title))
        for problem in assignment.problems:
            problem_cheatsheet_path = problem.path.joinpath(Paths.SOLUTION, Files.README)
            if problem_cheatsheet_path.exists():
                readme.write(markdown.header(make_problem_title(problem), level=2))
                readme.write(load_markdown(problem_cheatsheet_path, assignment, problem))


def build_solutions(assignment: Assignment, path: Path):
    """Compile only submission files of the solutions."""

    solution_path = path.joinpath(Paths.SOLUTION)
    solution_path.mkdir()

    for problem in assignment.problems:
        problem_solution_path = problem.path.joinpath(Paths.SOLUTION)
        if problem_solution_path.exists() and problem.submission:
            for submission_path in map(Path, problem.submission):
                relative_source_path = problem.path.joinpath(Paths.SOLUTION, *submission_path.parts[1:])
                relative_destination_path = solution_path.joinpath(problem.short, *submission_path.parts[1:])
                relative_destination_path.parent.mkdir(parents=True, exist_ok=True)
                files.copy(relative_source_path, relative_destination_path)


def build_key(assignment: Assignment, path: Path):
    """Compile cheatsheets."""

    key_path = path.joinpath(Paths.KEY)
    key_path.mkdir()
    build_cheatsheet(assignment, key_path)
    build_solutions(assignment, key_path)


def build_grading(assignment: Assignment, path: Path):
    """Compile rubrics."""

    grading_path = path.joinpath(Paths.GRADING)
    grading_path.mkdir()

    with grading_path.joinpath(Files.README).open("w") as rubric:
        rubric.write(markdown.header(f"{assignment.title} Rubric"))

        rubric.write(markdown.header("Assignment Rubric", level=2))
        rubric.write(load_markdown(Paths.FRAGMENT.joinpath("assignment_rubric"), assignment))

        for problem in assignment.problems:
            problem_grading_source_path = problem.path.joinpath(Paths.GRADING)
            if not problem_grading_source_path.exists():
                continue

            problem_grading_artifact_path = grading_path.joinpath(problem.short)
            files.copy(problem_grading_source_path, problem_grading_artifact_path)
            rubric.write(markdown.header(make_problem_title(problem), level=3))
            rubric.write(load_markdown(problem_grading_source_path.joinpath(Files.README), assignment, problem))
            files.delete_file(problem_grading_artifact_path.joinpath(Files.README))

        rubric.write(markdown.header("General Rubric", level=2))
        rubric.write(load_markdown(Paths.FRAGMENT.joinpath("progressive_rubric"), assignment))


BUILD_STEPS = (
    build_instructions,
    # build_skeleton,
    # build_key,
    # build_grading
)


def build(args: dict):
    """Build the assignment at a given path."""

    path = Path(args.pop("material")).absolute()
    environment = create_jinja2_environment(loader=jinja2.FileSystemLoader(str(path)))
    context = Context(environment, path, args)

    artifacts_path = path.parent.joinpath("artifacts")
    artifacts_path.mkdir(exist_ok=True)

    build_instructions(context, Assignment.load(path.joinpath("assignment", "hw1")), artifacts_path)
