import json
import jsonschema
import sys
from pathlib import Path

from .shared import *

ROOT = Path(__file__).absolute().parent


def validate_assignment_json(assignment_path: Path):
    """Validate with jsonschema."""

    with ROOT.joinpath("schema", "assignment.schema.json").open() as file:
        assignment_schema = json.load(file)
    with assignment_path.joinpath(Files.ASSIGNMENT).open() as file:
        assignment_json = json.load(file)

    try:
        jsonschema.validate(assignment_json, assignment_schema)
    except jsonschema.ValidationError as e:
        print(e, file=sys.stderr)


def validate_assignment(assignment_path: Path):
    """Validators per assignment."""

    validate_assignment_json(assignment_path)


def validate(material_path: Path):
    """Do a bunch of checks """

    for assignment_path in material_path.joinpath(Paths.ASSIGNMENT).glob("*/"):
        if not assignment_path.is_dir():
            continue
        validate_assignment(assignment_path)
