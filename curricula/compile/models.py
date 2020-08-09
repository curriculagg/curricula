import json

from pathlib import Path
from typing import List, Optional
from dataclasses import field

from ..models import Assignment, Problem
from ..shared import Files
from .exception import CompilationException


class CompilationProblem(Problem):
    """Add additional fields only used for build."""

    number: Optional[int]
    path: Path
    assignment: "CompilationAssignment"

    percentage: float = None

    @property
    def index_path(self) -> Path:
        return self.path.joinpath(Files.PROBLEM)

    @classmethod
    def read(
            cls,
            assignment: "CompilationAssignment",
            reference: dict,
            root: Path,
            number: int = None) -> "CompilationProblem":
        """Load a problem from the assignment path and reference."""

        path = root.joinpath(reference["path"])
        index_path = path.joinpath(Files.PROBLEM)

        try:
            with index_path.open() as file:
                data = json.load(file)
        except FileNotFoundError:
            raise CompilationException(message=f"No such path {index_path} for assignment {assignment.path}")
        except (PermissionError, OSError):
            raise CompilationException(message=f"Failed to read {index_path} for assignment {assignment.path}")
        except json.decoder.JSONDecodeError:
            raise CompilationException(message=f"Failed to deserialize {index_path} for assignment {assignment.path}")

        data["short"] = reference.get("short", data.get("short", path.parts[-1]))
        data["relative_path"] = reference.get("relative_path", data["short"])

        if "title" in reference:
            data["title"] = reference["title"]

        data["grading"]["enabled"] = reference["grading"].get("enabled", True)
        data["grading"]["weight"] = reference["grading"].get("weight", "1")
        data["grading"]["points"] = reference["grading"].get("points", "100")
        for category in "automated", "review", "manual":
            category_data = data["grading"][category]
            if category_data is None:
                continue

            if category in reference["grading"]:
                reference_category_data = reference["grading"][category]

                if "enabled" in reference_category_data:
                    category_data["enabled"] = reference_category_data
                if "weight" in reference_category_data:
                    category_data["weight"] = reference_category_data["weight"]
                if "points" in reference_category_data:
                    category_data["points"] = reference_category_data["points"]

            if "weight" not in category_data:
                category_data["weight"] = "1"
            if "points" not in category_data:
                category_data["points"] = "100"

        self = cls.load(data)

        # Convenience details for rendering
        self.assignment = assignment
        self.number = number
        self.path = path

        return self


class CompilationAssignment(Assignment):
    """Additional fields for build."""

    problems: List[CompilationProblem]
    path: Path = field(init=False)

    @property
    def index_path(self) -> Path:
        return self.path.joinpath(Files.ASSIGNMENT)

    @classmethod
    def read(cls, path: Path) -> "CompilationAssignment":
        """Load an assignment from a containing directory."""

        index_path = path.joinpath(Files.ASSIGNMENT)

        try:
            with index_path.open() as file:
                data = json.load(file)
        except FileNotFoundError:
            raise CompilationException(message=f"No such path {index_path}")
        except (PermissionError, OSError):
            raise CompilationException(message=f"Failed to read {index_path}")
        except json.decoder.JSONDecodeError:
            raise CompilationException(message=f"Failed to deserialize {index_path}")

        data["short"] = data.get("short", path.parts[-1])
        self = cls.load(data, problems=[])

        counter = 1
        total_weight = 0
        for reference in data.pop("problems"):
            problem = CompilationProblem.read(self, reference, path)
            if problem.grading.is_automated or problem.grading.is_review or problem.grading.is_manual:
                problem.number = counter
                counter += 1

            total_weight += problem.grading.weight
            self.problems.append(problem)

        for problem in self.problems:
            problem.percentage = problem.grading.weight / total_weight if total_weight > 0 else 0

        self.path = path

        return self
