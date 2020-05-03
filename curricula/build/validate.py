import json
import jsonschema
from pathlib import Path

from ..models import Assignment
from ..shared import *
from ..log import log

root = Path(__file__).absolute().parent

with root.joinpath("schema", "assignment.schema.json").open() as _file:
    ASSIGNMENT_SCHEMA = json.load(_file)
with root.joinpath("schema", "problem.schema.json").open() as _file:
    PROBLEM_SCHEMA = json.load(_file)


class ValidationException(Exception):
    """Raised while building models."""


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

    with assignment_path.joinpath(Files.ASSIGNMENT).open() as file:
        data = json.load(file)

    for problem_reference in data["problems"]:
        validate_problem_directory(assignment_path.joinpath(problem_reference["path"]))


def validate(assignment_path: Path):
    """Do a bunch of checks """

    validate_assignment(assignment_path)


def resolve_local(uri: str) -> dict:
    """Resolve a locally referenced schema."""

    with root.joinpath("schema", uri).open() as file:
        return json.load(file)


def create_validator(schema_path: Path) -> jsonschema.Draft7Validator:
    """Create a validator with a local resolver.

    For convenience, we'll simply override the handler for refs
    passed without a protocol prefix. This allows PyCharm to
    understand the ref location and do path checking in the source
    schema file.
    """

    resolver = jsonschema.RefResolver(
        base_uri=str(schema_path),
        referrer=ASSIGNMENT_SCHEMA,
        handlers={"": resolve_local})
    return jsonschema.Draft7Validator(schema=ASSIGNMENT_SCHEMA, resolver=resolver)


assignment_validator = create_validator(root / "schema" / "assignment.schema.json")
assignment_validator.validate({
    "authors": [
        {}
    ]
})
