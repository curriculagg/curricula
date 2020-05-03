import time
import datetime

from decimal import Decimal
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Any, Callable, TypeVar, Dict
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


def overwrite(over: dict, under: dict):
    """Overwrite a dictionary."""

    for key in over:
        if isinstance(over[key], dict) and key in under and isinstance(under[key], dict):
            overwrite(over[key], under[key])
        under[key] = over[key]


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
class ProblemGradingCategory(Model):
    """Data about weight, points, etc."""

    enabled: bool

    # Intrinsic
    name: Optional[str]
    minutes: Optional[float]

    # Overwrite
    weight: Decimal

    @classmethod
    def load(cls, data: dict) -> "ProblemGradingCategory":
        """Deserialize decimals."""

        return cls(
            enabled=data.get("enabled", True),
            weight=Decimal(data["weight"]),
            name=data["name"],
            minutes=data["minutes"],)

    def dump(self) -> dict:
        """Use string format."""

        return dict(
            enabled=self.enabled,
            weight=str(self.weight),
            name=self.name,
            minutes=self.minutes,)


@dataclass(eq=False)
class ProblemGrading(Model):
    """Data for each grading method."""

    enabled: bool
    weight: Decimal

    automated: ProblemGradingCategory
    review: ProblemGradingCategory
    manual: ProblemGradingCategory

    @classmethod
    def load(cls, data: dict) -> "ProblemGrading":
        """Deserialize each method."""

        return cls(
            enabled=data.get("enabled", True),
            weight=Decimal(data["weight"]),
            automated=some(data["automated"], ProblemGradingCategory.load),
            review=some(data["review"], ProblemGradingCategory.load),
            manual=some(data["manual"], ProblemGradingCategory.load),)

    def dump(self) -> dict:
        """Serialize with monad."""

        return dict(
            enabled=self.enabled,
            weight=str(self.weight),
            automated=some(self.automated, ProblemGradingCategory.dump),
            review=some(self.review, ProblemGradingCategory.dump),
            manual=some(self.manual, ProblemGradingCategory.dump),)


@dataclass(eq=False)
class Problem(Model):
    """All problem data."""

    # Overwrite
    short: str
    title: str
    relative_path: Path  # Most specific directory containing relevant files relative to assignment root

    # Defined in assignment reference
    grading: ProblemGrading

    # Intrinsic
    authors: List[Author]
    topics: List[str]
    notes: Optional[str] = None
    difficulty: Optional[str] = None

    @classmethod
    def load(cls, data: dict) -> "Problem":
        """Load directly from a dictionary."""

        return cls(
            short=data["short"],
            title=data["title"],
            relative_path=Path(data["relative_path"]),
            grading=ProblemGrading.load(data["grading"]),
            authors=list(map(Author.load, data["authors"])),
            topics=data["topics"],
            notes=data.get("notes"),
            difficulty=data.get("difficulty"),)

    def dump(self) -> dict:
        """Serialize 1:1."""

        return dict(
            short=self.short,
            title=self.title,
            relative_path=str(self.relative_path),
            grading=self.grading.dump(),
            authors=list(map(Author.dump, self.authors)),
            topics=self.topics,
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
    def load(cls, data: dict) -> "AssignmentGrading":
        """Load from serialized."""

        return cls(points=data["points"])


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
    grading: AssignmentGrading
    notes: Optional[str] = None
    meta: Meta = Meta()

    @classmethod
    def load(cls, data: dict, problems: List[Problem] = None) -> "Assignment":
        """Deserialize."""

        return cls(
            short=data["short"],
            title=data["title"],
            authors=list(map(Author.load, data["authors"])),
            dates=Dates.load(data["dates"]),
            problems=problems if problems is not None else list(map(Problem.load, data["problems"])),
            grading=AssignmentGrading.load(data["grading"]),
            notes=data.get("notes"),
            meta=Meta.load(data) if "meta" in data else Meta())

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
