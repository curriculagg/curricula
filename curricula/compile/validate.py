import json
import jsonschema
from pathlib import Path
from typing import Any

from ..shared import *
from ..log import log
from .exception import CompilationException

root = Path(__file__).absolute().parent


class ValidationException(Exception):
    """Raised while building models."""


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

    with schema_path.open() as file:
        schema = json.load(file)

    resolver = jsonschema.RefResolver(base_uri=str(schema_path), referrer=schema, handlers={"": resolve_local})
    return jsonschema.Draft7Validator(schema=schema, resolver=resolver)


assignment_validator = create_validator(root / "schema" / "assignment.schema.json")
problem_validator = create_validator(root / "schema" / "problem.schema.json")


def json_load_file(path: Path) -> Any:
    """Open a file and raise appropriate exceptions at on failure."""

    try:
        with path.open() as file:
            return json.load(file)
    except FileNotFoundError:
        raise CompilationException(message=f"No such path {path}")
    except (PermissionError, OSError):
        raise CompilationException(message=f"Failed to read {path}")
    except json.decoder.JSONDecodeError:
        raise CompilationException(message=f"Failed to deserialize {path}")


def validate_problem(problem_path: Path):
    """Validate with jsonschema."""

    data = json_load_file(problem_path.joinpath(Files.PROBLEM))

    try:
        problem_validator.validate(data)
    except jsonschema.ValidationError as exception:
        log.error(f"invalid schema in problem {problem_path}: {exception}")
        raise CompilationException(message=str(exception))


def validate_assignment(assignment_path: Path):
    """Validators per assignment."""

    data = json_load_file(assignment_path.joinpath(Files.ASSIGNMENT))

    try:
        assignment_validator.validate(data)
    except jsonschema.ValidationError as exception:
        log.error(f"invalid schema in assignment {assignment_path}: {exception}")
        raise CompilationException(message=str(exception))

    for problem_reference in data["problems"]:
        validate_problem(assignment_path.joinpath(problem_reference["path"]))


def validate(assignment_path: Path):
    """Do a bunch of checks """

    validate_assignment(assignment_path)
