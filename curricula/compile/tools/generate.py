import json
import jsonschema
import re
from pathlib import Path
from typing import Callable

from ...shared import Files
from ..validate import assignment_validator, problem_validator


Validator = Callable[[str], bool]


def validate_not_empty(string: str) -> bool:
    if len(string) == 0:
        print("Must not be empty!")
        return False
    return True


def validate_datetime(string: str) -> bool:
    if re.match(r"^\d{4}-\d{1,2}-\d{1,2} \d{2}:\d{2}:\d{2}$", string) is None:
        print("Must be of the form YYYY-MM-DD HH:MM:SS!")
        return False
    return True


def validate_datetime_nullable(string: str) -> bool:
    if len(string) == 0:
        return True
    return validate_datetime(string)


def validate_integral(string: str) -> bool:
    if not string.isnumeric():
        print("Must be a positive integer!")
        return False
    return True


def validate_float(string: str) -> bool:
    try:
        float(string)
    except ValueError:
        return False
    return True


def validate_email(string: str) -> bool:
    if re.match(r"^.+@.+\..+$", string) is None:
        print("Invalid email!")
        return False
    return True


def validate_boolean(string: str) -> bool:
    if string.lower() not in ("y", "n", "yes", "no"):
        print("Must be (y)es or (n)o!")
        return False
    return True


def validate_weight(string: str) -> bool:
    if re.match(r"\d+(\.\d+)?", string) is None:
        print("Must be a float!")
        return False
    if not 0 <= float(string) <= 1:
        print("Must be between 0 and 1 inclusive!")
        return False
    return True


def validated_input(prompt: str = "", *validators: Validator) -> str:
    """Input until validated."""

    while True:
        response = input(prompt)
        if all(validator(response) for validator in validators):
            return response


def input_assignment_json() -> dict:
    """Encapsulate input logic."""

    while True:
        assignment_json = {
            "title": validated_input("Assignment title: ", validate_not_empty),
            "authors": [
                {
                    "name": validated_input("Author name: ", validate_not_empty),
                    "email": validated_input("Author email (address@domain.com): ", validate_email)
                }
            ],
            "dates": {
                "assigned": validated_input("Assigned (YYYY-MM-DD HH:MM:SS or empty): ", validate_datetime_nullable),
                "due": validated_input("Due (YYYY-MM-DD HH:MM:SS or empty): ", validate_datetime_nullable),
                "deadline": validated_input("Deadline (YYYY-MM-DD HH:MM:SS or empty): ", validate_datetime_nullable),
            },
            "problems": [],
            "grading": {
                "points": validated_input("Total points: ", validate_integral)
            }
        }

        for field in "assigned", "due", "deadline":
            if len(assignment_json["dates"][field]) == 0:
                assignment_json["dates"][field] = None

        try:
            assignment_validator.validate(assignment_json)
        except jsonschema.ValidationError as exception:
            print(exception)
        else:
            return assignment_json


def generate_assignment_interactive(assignment_path: Path):
    """Generate a new assignment."""

    try:
        assignment_json = input_assignment_json()
    except KeyboardInterrupt:
        print("Cancelling...")
        return

    assignment_path.mkdir(parents=True, exist_ok=True)
    with assignment_path.joinpath(Files.ASSIGNMENT).open("w") as file:
        json.dump(assignment_json, file, indent=2)

    print(f"Created assignment {assignment_path.parts[-1]}!")


def input_problem_json() -> dict:
    while True:
        problem_json = {
            "title": validated_input("Problem title: ", validate_not_empty),
            "authors": [
                {
                    "name": validated_input("Author name: ", validate_not_empty),
                    "email": validated_input("Author email (address@domain.com): ", validate_email)
                }
            ],
            "topics": [
                *map(str.strip, input("Optional topics (separated by comma): ").split(","))
            ],
            "grading": {
                "points": validated_input("Total points: ", validate_integral),
                "automated": None,
                "review": None,
                "manual": None,
            }
        }

        for category in "automated", "review", "manual":
            if validated_input(f"Requires {category} grading (y/n): ", validate_boolean).lower().startswith("y"):
                problem_json["grading"][category] = {
                    "weight": validated_input(f"Weight for {category}: ", validate_float)
                }

        try:
            problem_validator.validate(problem_json)
        except jsonschema.ValidationError as exception:
            print(exception)
        else:
            return problem_json


def generate_problem_interactive(assignment_path: Path, problem_relative_path: Path):
    """Generate an assignment within the assignment."""

    with assignment_path.joinpath(Files.ASSIGNMENT).open("r") as file:
        assignment_json = json.load(file)

    for existing_problem_json in assignment_json["problems"]:
        if Path(existing_problem_json["path"]).parts[-1] == problem_relative_path.parts[-1]:
            print("A problem with the same short is already in the assignment!")
            return

    try:
        problem_json = input_problem_json()
    except KeyboardInterrupt:
        print("Cancelling...")
        return

    while True:
        assignment_json["problems"].append({
            "path": str(problem_relative_path),
            "grading": {
                "weight": validated_input("Problem weight: ", validate_float)
            }
        })

        try:
            assignment_validator.validate(assignment_json)
        except jsonschema.ValidationError as exception:
            print(exception)
        else:
            break

    with assignment_path.joinpath(Files.ASSIGNMENT).open("w") as file:
        json.dump(assignment_json, file, indent=2)

    problem_path = assignment_path.joinpath(problem_relative_path)
    problem_path.mkdir(parents=True, exist_ok=True)
    with problem_path.joinpath(Files.PROBLEM).open("w") as file:
        json.dump(problem_json, file, indent=2)

    print(f"Created problem {problem_relative_path}!")
