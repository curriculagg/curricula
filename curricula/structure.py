from pathlib import Path
from typing import Iterator

__all__ = (
    "Paths",
    "Files",
    "InstructionsArtifact",
    "ResourcesArtifact",
    "SolutionArtifact",
    "GradingArtifact",
    "Artifacts")


class Paths:
    DOT = Path()

    INSTRUCTIONS = Path("instructions")
    RESOURCES = Path("resources")
    SOLUTION = Path("solution")
    GRADING = Path("grading")

    ASSIGNMENT = Path("assignment")
    PROBLEM = Path("problem")
    ARTIFACTS = Path("artifacts")
    ASSETS = Path("assets")
    INCLUDE = Path("grade", "include")

    @classmethod
    def glob_assignments(cls, material_path: Path) -> Iterator[Path]:
        """Provide a unified search for assignments."""

        for path in material_path.joinpath(cls.ASSIGNMENT).glob("*/"):
            if path.is_dir():
                yield path


class Files:
    README = "README.md"
    ASSIGNMENT = "assignment.json"
    PROBLEM = "problem.json"
    GRADING = "grading.json"
    TESTS = "tests.py"
    INDEX = "index.json"


class Artifact:
    path: Path

    def __init__(self, path: Path):
        self.path = path


class InstructionsArtifact(Artifact):
    """Instructions and assets."""


class ResourcesArtifact(Artifact):
    """Assignment skeleton code."""


class SolutionArtifact(Artifact):
    """Example solution."""


class GradingArtifact(Artifact):
    """Contains metadata about the assignment and grading scripts."""

    @property
    def index_path(self) -> Path:
        return self.path.joinpath(Files.INDEX)


class Artifacts:
    """Bundled artifacts produced by curricula_compile."""

    instructions: InstructionsArtifact
    resources: ResourcesArtifact
    solution: SolutionArtifact
    grading: GradingArtifact

    def __init__(self, path: Path):
        """Initialize each artifact on its corresponding path"""

        self.instructions = InstructionsArtifact(path.joinpath(Paths.INSTRUCTIONS))
        self.resources = ResourcesArtifact(path.joinpath(Paths.RESOURCES))
        self.solution = SolutionArtifact(path.joinpath(Paths.SOLUTION))
        self.grading = GradingArtifact(path.joinpath(Paths.GRADING))
