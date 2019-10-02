from pathlib import Path

__all__ = ("Paths", "Files")


class Paths:
    ARTIFACTS = Path("artifacts")
    INSTRUCTIONS = Path("site")
    SKELETON = Path("skeleton")
    SOLUTION = Path("solution")
    GRADING = Path("grading")
    ASSETS = Path("assets")


class Files:
    README = "README.md"
    ASSIGNMENT = "assignment.json"
    PROBLEM = "problem.json"
