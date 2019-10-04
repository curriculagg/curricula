import importlib
import json
import sys
from typing import Dict
from pathlib import Path
from dataclasses import dataclass

from .grader import Grader
from ..mapping.shared import *


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
        for problem_short in schema["automated"]:
            sys.path.insert(0, str(grading_path.joinpath(problem_short)))
            module = importlib.import_module("tests")
            graders[problem_short] = module.grade
            sys.path.pop(0)

        return Manager(graders)
