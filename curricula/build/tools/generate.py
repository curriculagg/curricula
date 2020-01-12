import json
import jsonschema
from pathlib import Path

from ...shared import Files
from .. import validate


def generate_assignment_interactive(assignment_path: Path):
    """Generate a new assignment."""

    while True:
        try:
            assignment_json = {
                "title": input("Assignment title: "),
                "authors": [],
                "dates": {
                    "assigned": input("Date assigned (YYYY-MM-DD HH:MM:SS): "),
                    "due": input("Date due (YYYY-MM-DD HH:MM:SS): ")
                },
                "problems": []
            }
        except KeyboardInterrupt:
            print("Cancelling...")
            return

        try:
            jsonschema.validate(assignment_json, validate.ASSIGNMENT_SCHEMA)
        except jsonschema.ValidationError as exception:
            print(exception)
        else:
            break

    assignment_path.mkdir(parents=True, exist_ok=True)
    with assignment_path.joinpath(Files.ASSIGNMENT).open("w") as file:
        json.dump(assignment_json, file)
