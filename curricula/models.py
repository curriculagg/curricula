import time
import datetime
import json

from decimal import Decimal
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Any, Callable, TypeVar
from abc import ABC, abstractmethod

from .shared import *

TZ = datetime.timezone(offset=datetime.timedelta(seconds=time.timezone))


def parse_datetime(s: str) -> datetime.datetime:
    """Deserialize our standard format."""

    return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=TZ)


def dump_datetime(d: datetime) -> str:
    """Serialize back."""

    return d.strftime("%Y-%m-%d %H:%M:%S")


T = TypeVar("T")


def some(value: Optional[T], method: Callable[[T], Any]) -> Optional[T]:
    """Probably a monad, right?"""

    if value is None:
        return value
    return method(value)


@dataclass(eq=False)
class Model(ABC):
    """Provide some default behaviors."""

    def dump(self) -> dict:
        return asdict(self)

    @classmethod
    @abstractmethod
    def load(cls, data: dict) -> "Model":
        """Load the model from serialized data."""


@dataclass(eq=False)
class Author(Model):
    """Name and email."""

    name: str
    email: str

    @classmethod
    def load(cls, data: dict) -> "Author":
        """Deserialize and check for errors."""

        return Author(name=data.pop("name"), email=data.pop("email"))


@dataclass(eq=False)
class ProblemGradingMethod(Model):
    """Data about weight, points, etc."""

    weight: Decimal
    points: Decimal

    @classmethod
    def load(cls, grading: dict) -> "ProblemGradingMethod":
        """Deserialize decimals."""

        return cls(
            weight=Decimal(grading["weight"]),
            points=Decimal(grading["points"]),)

    def dump(self) -> dict:
        """Use string format."""

        return dict(
            weight=str(self.weight),
            points=str(self.points),)


@dataclass(eq=False)
class ProblemGrading(Model):
    """These are the only possible kinds of grading."""

    minutes: int
    automated: Optional[ProblemGradingMethod]
    review: Optional[ProblemGradingMethod]
    manual: Optional[ProblemGradingMethod]

    @classmethod
    def load(cls, grading: dict) -> "ProblemGrading":
        """Load methods from serialized."""

        return cls(
            minutes=grading["minutes"],
            automated=some(grading["automated"], ProblemGradingMethod.load),
            review=some(grading["review"], ProblemGradingMethod.load),
            manual=some(grading["manual"], ProblemGradingMethod.load),)

    def dump(self) -> dict:
        """Serialize methods."""

        return dict(
            minutes=self.minutes,
            automated=some(self.automated, ProblemGradingMethod.dump),
            review=some(self.review, ProblemGradingMethod.dump),
            manual=some(self.manual, ProblemGradingMethod.dump),)


@dataclass(eq=False)
class Problem(Model):
    """All problem data."""

    short: str
    relative_path: Path  # Most specific directory containing relevant files

    title: str
    authors: List[Author]
    topics: List[str]

    grading: ProblemGrading

    notes: Optional[str] = None
    difficulty: Optional[str] = None

    @classmethod
    def load(cls, data: dict, **overwrite) -> "Problem":
        """Load directly from a dictionary."""

        return cls(
            short=overwrite.get("relative_path") or data["short"],
            relative_path=overwrite.get("relative_path") or data["relative_path"],
            title=overwrite.get("relative_path") or data["title"],
            authors=list(map(Author.load, data["authors"])),
            topics=data["topics"],
            grading=ProblemGrading.load(data["grading"]),
            notes=data["notes"],
            difficulty=data["difficulty"],)

    def dump(self) -> dict:
        """Serialize 1:1."""

        return dict(
            short=self.short,
            relative_path=self.relative_path,
            title=self.title,
            authors=list(map(Author.dump, self.authors)),
            topics=self.topics,
            grading=self.grading.dump(),
            notes=self.notes,
            difficulty=self.difficulty,)


@dataclass(eq=False)
class Dates(Model):
    """Assignment dates."""

    assigned: datetime.datetime
    due: datetime.datetime

    @classmethod
    def load(cls, data: dict) -> "Dates":
        """Convert to datetime."""

        return cls(
            assigned=parse_datetime(data["assigned"]),
            due=parse_datetime(data["due"]),)

    def dump(self) -> dict:
        """Specifically serialize the datetime."""

        return dict(
            assigned=dump_datetime(self.assigned),
            due=dump_datetime(self.due),)


@dataclass(eq=False)
class AssignmentGrading(Model):
    """Weights and points."""

    points: int

    @classmethod
    def load(cls, grading: dict) -> "AssignmentGrading":
        """Load from serialized."""

        return cls(**grading)


@dataclass(eq=False)
class Meta(Model):
    """Metadata about an assignment."""

    built: datetime.datetime = field(default_factory=datetime.datetime.now)
    version: str = version

    @classmethod
    def load(cls, data: dict) -> "Meta":
        """Deserialize datetime."""

        return cls(
            built=parse_datetime(data["built"]),
            version=data["version"],)

    def dump(self) -> dict:
        """Serialize the datetime here too."""

        return dict(
            built=dump_datetime(self.built),
            version=version,)


@dataclass(eq=False)
class Assignment(Model):
    """Contains assignment metadata."""

    short: str
    title: str
    authors: List[Author]
    dates: Dates
    problems: List[Problem]
    notes: Optional[str] = None
    meta: Meta = Meta()

    @classmethod
    def load(cls, data: dict) -> "Assignment":
        """Deserialize."""



    @classmethod
    def read(cls, path: Path) -> "Assignment":
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
            self.problems.append(Problem.read(reference, path, number))

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
