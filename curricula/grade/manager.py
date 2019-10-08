import importlib
import json
import sys
from typing import Dict, List
from pathlib import Path
from dataclasses import dataclass

from .grader import Grader
from .report import Report
from .resource import Context
from ..mapping.shared import *
from ..mapping.models import Problem


def import_grader(tests_path: Path, grader_name: str = "grader") -> Grader:
    """Import a grader from a tests file."""

    sys.path.insert(0, str(tests_path.parent))
    base_name = tests_path.parts[-1]
    if base_name.endswith(".py"):
        base_name = base_name[:-3]

    module = importlib.import_module(base_name)
    grader = getattr(module, grader_name)
    sys.path.pop(0)

    return grader


def generate_grading_schema(grading_path: Path, problems: List[Problem]) -> dict:
    """Generate a JSON schema describing the grading package.

    This method requires the grading artifact to already have been
    aggregated, as it has to access the individual problem graders to
    dump their task summaries.
    """

    result = {}
    for problem in problems:
        grader = import_grader(grading_path.joinpath(problem.short, Files.TESTS))
        result[problem.short] = dict(percentage=problem.percentage, tasks=grader.dump())
    return result


@dataclass
class Manager:
    """A container for multiple graders in an assignment."""

    graders: Dict[str, Grader]

    @classmethod
    def load(cls, grading_path: Path) -> "Manager":
        """Load a manager from a grading artifact in the file system."""

        with grading_path.joinpath(Files.GRADING).open() as file:
            schema = json.load(file)

        graders = {}
        for problem_short in schema:
            graders[problem_short] = import_grader(grading_path.joinpath(problem_short, Files.TESTS))

        return Manager(graders)

    def run(self, target_path: Path, **options) -> Dict[str, Report]:
        """Run all tests on a submission and return a dict of results."""

        reports = {}
        for problem_short, grader in self.graders.items():
            context = Context(target_path, **options)
            reports[problem_short] = grader.run(context=context)
        return reports
