from pathlib import Path

__all__ = ("Paths", "Files")


class Paths:
    ARTIFACTS = Path("artifacts")
    INSTRUCTIONS = Path("site")
    RESOURCES = Path("resources")
    SOLUTION = Path("solution")
    GRADING = Path("grading")
    ASSETS = Path("assets")


class Files:
    README = "README.md"
    ASSIGNMENT = "assignment.json"
    PROBLEM = "problem.json"
