from pathlib import Path

__all__ = ("Paths", "Files")


class Paths:
    ARTIFACTS = Path("artifacts")
    INSTRUCTIONS = Path("instructions")
    RESOURCES = Path("resources")
    SOLUTION = Path("solution")
    GRADING = Path("grading")
    ASSETS = Path("assets")


class Files:
    README = "README.md"
    ASSIGNMENT = "assignment.json"
    PROBLEM = "problem.json"
    GRADING = "grading.json"
    TESTS = "tests.py"
