import importlib.util
import json
import sys
from pathlib import Path
from typing import List, Optional
from dataclasses import field

from ..models import Assignment, Problem
from ..shared import Files
from .task import Task
from .grader import Grader
from .report import AssignmentReport


def import_grader(grading_path: Path, grader_name: str = "grader") -> Grader:
    """Import a grader from a tests file."""

    # Try to import as a module
    if grading_path.joinpath("__init__.py").is_file():
        name = f"_curricula_grading_{grading_path.parts[-1]}"
        spec = importlib.util.spec_from_file_location(name, str(grading_path.joinpath("__init__.py")))
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module

    # Otherwise there's a tests.py
    else:
        name = f"_curricula_grading_{grading_path.parts[-1]}_tests"
        spec = importlib.util.spec_from_file_location(name, str(grading_path.joinpath("tests.py")))
        module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)
    grader = getattr(module, grader_name)

    return grader


class GradingProblem(Problem):
    """Additional details for grading."""

    path: Path = field(init=False)
    grader: Grader = field(init=False)

    @classmethod
    def read(cls, data: dict, path: Path) -> "GradingProblem":
        """Import the grader."""

        self = GradingProblem.load(data)
        self.path = path
        self.grader = import_grader(path)
        return self


class GradingAssignment(Assignment):
    """Additional details for grading."""

    problems: List[GradingProblem]

    @classmethod
    def read(cls, path: Path) -> "GradingAssignment":
        """Read the assignment.json and rebuild the models."""

        with path.joinpath(Files.INDEX).open("r") as file:
            data = json.load(file)

        problems = []
        for problem_data in data.pop("problems"):
            problems.append(GradingProblem.read(problem_data, path.joinpath(problem_data["short"])))

        return GradingAssignment.load(data, problems=problems)
