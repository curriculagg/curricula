import datetime
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List

from ..shared import *


@dataclass
class Author:
    """Name and email."""

    name: str
    email: str

    def dump(self) -> dict:
        return asdict(self)


@dataclass
class Dates:
    """Assignment dates."""

    assigned: datetime.datetime
    due: datetime.datetime

    def __init__(self, assigned: str, due: str):
        """Convert to datetime."""

        self.assigned = datetime.datetime.strptime(assigned, "%Y-%m-%d %H:%M:%S")
        self.due = datetime.datetime.strptime(due, "%Y-%m-%d %H:%M:%S")

    def dump(self) -> dict:
        return dict(
            assigned=self.assigned.strftime("%Y-%m-%d %H:%M:%S"),
            due=self.due.strftime("%Y-%m-%d %H:%M:%S"))


@dataclass
class Grading:
    """Grading description."""

    minutes: int
    automated: bool
    review: bool
    manual: bool

    def dump(self) -> dict:
        return asdict(self)


@dataclass
class Problem:
    """All problem data."""

    assignment: "Assignment"

    path: Path
    short: str
    number: int
    percentage: float
    directory: str  # Most specific directory containing relevant files

    title: str
    authors: List[Author]
    topics: List[str]
    grading: Grading
    notes: Optional[str] = None
    difficulty: Optional[str] = None

    @classmethod
    def load(cls, assignment: "Assignment", root: Path, reference: dict, number: int) -> "Problem":
        """Load a problem from the assignment path and reference."""

        path = root.joinpath(reference["path"])
        short = path.parts[-1]
        with path.joinpath(Files.PROBLEM).open() as file:
            data = json.load(file)

        authors = list(Author(**author) for author in data.pop("authors"))
        grading = Grading(**data.pop("grading"))
        percentage = reference["percentage"]
        directory = reference["directory"] if "directory" in reference else short

        return cls(
            assignment=assignment,
            path=path,
            short=short,
            number=number,
            percentage=percentage,
            authors=authors,
            grading=grading,
            directory=directory,
            **data)

    def dump(self) -> dict:
        return dict(
            short=self.short,
            percentage=self.percentage,
            title=self.title,
            authors=[author.dump() for author in self.authors],
            topics=self.topics,
            notes=self.notes,
            difficulty=self.difficulty,
            grading=self.grading.dump(),
            directory=self.directory)


@dataclass
class Assignment:
    """Contains assignment metadata."""

    path: Path
    short: str

    title: str
    authors: List[Author]
    dates: Dates
    problems: List[Problem]
    notes: Optional[str] = None

    @classmethod
    def load(cls, path: Path) -> "Assignment":
        """Load an assignment from a containing directory."""

        short = path.parts[-1]
        with path.joinpath(Files.ASSIGNMENT).open() as file:
            data = json.load(file)

        authors = list(Author(**author) for author in data.pop("authors"))
        dates = Dates(**data.pop("dates"))
        problem_references = data.pop("problems")

        self = cls(path, short, authors=authors, dates=dates, problems=[], **data)

        counter = 1
        for reference in problem_references:
            number = None
            if reference["percentage"] > 0:
                number = counter
                counter += 1
            self.problems.append(Problem.load(self, path, reference, number))

        return self

    def dump(self) -> dict:
        """Dump the assignment to JSON.

        This method is not symmetric to load, and should therefore
        probably not be called dump. It is intended for use in
        generating the grading schema.
        """

        return dict(
            short=self.short,
            title=self.title,
            authors=[author.dump() for author in self.authors],
            dates=self.dates.dump(),
            problems=[problem.dump() for problem in self.problems],
            notes=self.notes)
