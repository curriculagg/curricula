import json

from pathlib import Path
from typing import List
from dataclasses import field

from ..models import Assignment, Problem
from ..shared import Files


class CompilationProblem(Problem):
    """Add additional fields only used for build."""

    number: int
    path: Path
    assignment: "CompilationAssignment"

    percentage: float = None

    @classmethod
    def read(cls, assignment: "CompilationAssignment", reference: dict, root: Path, number: int) -> "CompilationProblem":
        """Load a problem from the assignment path and reference."""

        path = root.joinpath(reference["path"])
        with path.joinpath(Files.PROBLEM).open() as file:
            data = json.load(file)

        data["short"] = reference.get("short", data.get("short", path.parts[-1]))
        data["relative_path"] = reference.get("relative_path", path.parts[-1])

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

    @classmethod
    def read(cls, path: Path) -> "CompilationAssignment":
        """Load an assignment from a containing directory."""

        with path.joinpath(Files.ASSIGNMENT).open() as file:
            data = json.load(file)

        data["short"] = data.get("short", path.parts[-1])
        self = cls.load(data, problems=[])

        counter = 1
        total_weight = 0
        for reference in data.pop("problems"):
            number = None
            if any(filter(None, reference["grading"])):
                number = counter
                counter += 1

            problem = CompilationProblem.read(self, reference, path, number)
            total_weight += problem.grading.weight
            self.problems.append(problem)

        for problem in self.problems:
            problem.percentage = problem.grading.weight / total_weight if total_weight > 0 else 0

        self.path = path

        return self
