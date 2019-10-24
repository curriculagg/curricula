import datetime
import json
from decimal import Decimal
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List

from .shared import *


@dataclass
class Author:
    """Name and email."""

    name: str
    email: str


@dataclass
class Dates:
    """Assignment dates."""

    assigned: datetime.datetime
    deadline: datetime.datetime

    def __init__(self, assigned: str, deadline: str):
        """Convert to datetime."""

        self.assigned = datetime.datetime.strptime(assigned, "%Y-%m-%d %H:%M:%S")
        self.deadline = datetime.datetime.strptime(deadline, "%Y-%m-%d %H:%M:%S")


@dataclass
class Grading:
    """Grading description."""

    minutes: int
    process: List[str]


@dataclass
class Problem:
    """All problem data."""

    assignment: "Assignment"

    path: Path
    short: str
    number: int
    percentage: Decimal

    title: str
    authors: List[Author]
    topics: List[str]
    notes: Optional[str] = None
    difficulty: Optional[str] = None
    submission: Optional[List[str]] = None
    grading: Optional[Grading] = None

    @classmethod
    def load(cls, assignment: "Assignment", root: Path, reference: dict, number: int) -> "Problem":
        """Load a problem from the assignment path and reference."""

        path = root.joinpath(reference["path"])
        short = path.parts[-1]
        with path.joinpath(Files.PROBLEM).open() as file:
            data = json.load(file)

        authors = list(Author(**author) for author in data.pop("authors"))
        grading = Grading(**data.pop("grading")) if "grading" in data else None
        percentage = Decimal(reference["percentage"])
        return cls(assignment, path, short, number, percentage, authors=authors, grading=grading, **data)


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
