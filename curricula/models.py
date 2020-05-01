import time
import datetime
import json
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional, List

from .shared import *

TZ = datetime.timezone(offset=datetime.timedelta(seconds=time.timezone))


def parse_datetime(s: str) -> datetime.datetime:
    return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=TZ)


def dump_datetime(d: datetime) -> str:
    return d.strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class Author:
    """Name and email."""

    name: str
    email: str

    def dump(self) -> dict:
        return asdict(self)


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

    short: str
    number: int
    directory: str  # Most specific directory containing relevant files

    title: str
    authors: List[Author]
    topics: List[str]
    grading: Grading
    notes: Optional[str] = None
    difficulty: Optional[str] = None

    @classmethod
    def load_from_directory(cls, assignment: "Assignment", root: Path, reference: dict, number: int) -> "Problem":
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
class Dates:
    """Assignment dates."""

    assigned: datetime.datetime
    due: datetime.datetime

    def __init__(self, assigned: str, due: str):
        """Convert to datetime."""

        self.assigned = parse_datetime(assigned)
        self.due = parse_datetime(due)

    def dump(self) -> dict:
        """Specifically serialize the datetime."""

        return dict(assigned=dump_datetime(self.assigned), due=dump_datetime(self.due))


@dataclass
class Meta:
    """Metadata about an assignment."""

    built: datetime.datetime = field(default_factory=datetime.datetime.now)
    version: str = version

    def dump(self) -> dict:
        """Serialize the datetime here too."""

        return dict(built=dump_datetime(self.built), version=version)


@dataclass
class Assignment:
    """Contains assignment metadata."""

    short: str
    title: str
    authors: List[Author]
    dates: Dates
    problems: List[Problem]
    notes: Optional[str] = None
    meta: Meta = Meta()

    @classmethod
    def load_from_directory(cls, path: Path) -> "Assignment":
        """Load an assignment from a containing directory."""

        short = path.parts[-1]
        with path.joinpath(Files.ASSIGNMENT).open() as file:
            data = json.load(file)

        authors = list(Author(**author) for author in data.pop("authors"))
        dates = Dates(**data.pop("dates"))
        problem_references = data.pop("problems")

        self = cls(short, authors=authors, dates=dates, problems=[], **data)

        counter = 1
        for reference in problem_references:
            number = None
            if reference["percentage"] > 0:
                number = counter
                counter += 1
            self.problems.append(Problem.load_from_directory(self, path, reference, number))

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
            notes=self.notes,
            meta=self.meta.dump())
