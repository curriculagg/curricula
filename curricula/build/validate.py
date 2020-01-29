import json
import jsonschema
from pathlib import Path

from .models import Assignment
from ..shared import *
from ..log import log

root = Path(__file__).absolute().parent

with root.joinpath("schema", "assignment.schema.json").open() as _file:
    ASSIGNMENT_SCHEMA = json.load(_file)
with root.joinpath("schema", "problem.schema.json").open() as _file:
    PROBLEM_SCHEMA = json.load(_file)


def validate_problem_directory(problem_path: Path):
    """Validate with jsonschema."""

    try:
        jsonschema.validate(problem_path.joinpath(Files.PROBLEM).read_text(), PROBLEM_SCHEMA)
    except jsonschema.ValidationError as exception:
        log.error(f"invalid schema in problem {problem_path}: {exception}")
        raise


def validate_assignment_directory(assignment_path: Path):
    """Validate with jsonschema."""

    try:
        jsonschema.validate(assignment_path.joinpath(Files.ASSIGNMENT).read_text(), PROBLEM_SCHEMA)
    except jsonschema.ValidationError as exception:
        log.error(f"invalid schema in assignment {assignment_path}: {exception}")
        raise


def validate_assignment(assignment_path: Path):
    """Validators per assignment."""

    validate_assignment_directory(assignment_path)

    assignment = Assignment.load(assignment_path)
    for problem in assignment.problems:
        validate_problem_directory(problem.path)


def validate(assignment_path: Path):
    """Do a bunch of checks """

    validate_assignment(assignment_path)
