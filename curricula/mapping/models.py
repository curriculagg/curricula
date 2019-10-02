import datetime
import json
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

        self.assigned = datetime.datetime.strptime(assigned, "%Y-%m-%d %H:%M")
        self.deadline = datetime.datetime.strptime(deadline, "%Y-%m-%d %H:%M")


@dataclass
class Grading:
    """Grading description."""

    minutes: int
    process: List[str]


@dataclass
class Problem:
    """All problem data."""

    path: Path
    short: str
    number: int
    percentage: float

    title: str
    authors: List[Author]
    topics: List[str]
    notes: Optional[str] = None
    difficulty: Optional[str] = None
    submission: Optional[List[str]] = None
    grading: Optional[Grading] = None

    @classmethod
    def load(cls, root: Path, reference: dict, number: int):
        """Load a problem from the assignment path and reference."""

        path = root.joinpath(reference["path"])
        short = path.parts[-1]
        with path.joinpath(Files.PROBLEM).open() as file:
            data = json.load(file)

        authors = list(Author(**author) for author in data.pop("authors"))
        grading = Grading(**data.pop("grading")) if "grading" in data else None
        percentage = reference["percentage"]
        return cls(path, short, number, percentage, authors=authors, grading=grading, **data)


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
    def load(cls, path: Path):
        """Load an assignment from a containing directory."""

        short = path.parts[-1]
        with path.joinpath(Files.ASSIGNMENT).open() as file:
            data = json.load(file)

        authors = list(Author(**author) for author in data.pop("authors"))
        dates = Dates(**data.pop("dates"))

        counter = 1
        problems = []
        for reference in data.pop("problems"):
            number = None
            if reference["percentage"] > 0:
                number = counter
                counter += 1
            problems.append(Problem.load(path, reference, number))

        return cls(path, short, authors=authors, dates=dates, problems=problems, **data)
