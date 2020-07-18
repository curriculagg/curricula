import importlib.util
import json
import sys
from pathlib import Path
from typing import List
from dataclasses import field
from decimal import Decimal
from functools import lru_cache

from ..models import Assignment, Problem, ProblemGrading, Author
from ..shared import Files
from .grader import Grader


def import_grader(grading_path: Path, problem: "GradingProblem", grader_name: str = "grader") -> Grader:
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
    grader.problem = problem

    return grader


class GradingProblemGrading(ProblemGrading):
    """Override to add grader-specific computations."""

    problem: "GradingProblem"

    @property
    @lru_cache(maxsize=1)
    def point_ratio(self) -> Decimal:
        return self.points / self.problem.grader.test.weight


class GradingProblem(Problem):
    """Additional details for grading."""

    path: Path = field(init=False)
    grader: Grader = field(init=False)
    grading: GradingProblemGrading

    @classmethod
    def read(cls, data: dict, path: Path) -> "GradingProblem":
        """Import the grader."""

        self = GradingProblem.load(data)
        self.path = path
        if self.grading.is_automated:
            self.grader = import_grader(path, self)
        return self


class GradingAssignment(Assignment):
    """Additional details for grading."""

    path: Path

    problems: List[GradingProblem]

    @classmethod
    def read(cls, path: Path) -> "GradingAssignment":
        """Read the assignment.json and rebuild the models."""

        with path.joinpath(Files.INDEX).open("r") as file:
            data = json.load(file)

        problems = []
        for problem_data in data.pop("problems"):
            problems.append(GradingProblem.read(
                data=problem_data,
                path=path.joinpath(problem_data["short"])))

        assignment = GradingAssignment.load(data, problems=problems)
        assignment.path = path

        return assignment
