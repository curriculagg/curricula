import time
import datetime

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
class ProblemGradingCategory(Model):
    """Data about weight, points, etc."""

    enabled: bool

    # Intrinsic
    name: Optional[str]
    minutes: Optional[float]

    # Overwrite
    weight: Decimal
    points: Decimal

    @classmethod
    def load(cls, data: dict) -> "ProblemGradingCategory":
        """Deserialize decimals."""

        return cls(
            enabled=data.get("enabled", True),
            name=data["name"],
            minutes=data.get("minutes"),
            weight=Decimal(data["weight"]),
            points=Decimal(data["points"]),)

    def dump(self) -> dict:
        """Use string format."""

        return dict(
            enabled=self.enabled,
            name=self.name,
            minutes=self.minutes,
            weight=str(self.weight),
            points=str(self.points),)


class ProblemGradingAutomated(ProblemGradingCategory):
    """Additional properties specific to automated grading."""

    tasks: List


@dataclass(eq=False)
class ProblemGrading(Model):
    """Data for each grading method."""

    problem: "Problem"

    enabled: bool
    weight: Decimal
    points: Decimal

    automated: ProblemGradingCategory
    review: ProblemGradingCategory
    manual: ProblemGradingCategory

    @property
    def is_automated(self) -> bool:
        return self.automated is not None and self.automated.enabled

    @property
    def is_review(self) -> bool:
        return self.review is not None and self.review.enabled

    @property
    def is_manual(self) -> bool:
        return self.manual is not None and self.manual.enabled

    def percentage(self) -> Decimal:
        return self.weight / self.problem.assignment.grading.weight()

    @classmethod
    def load(cls, data: dict, problem: "Problem" = None) -> "ProblemGrading":
        """Deserialize each method."""

        if data["automated"] is not None and data["automated"].get("name") is None:
            data["automated"]["name"] = "Automated Tests"
        if data["review"] is not None and data["review"].get("name") is None:
            data["review"]["name"] = "Code Review"
        if data["manual"] is not None and data["manual"].get("name") is None:
            data["manual"]["name"] = "Manual Grading"

        return cls(
            problem=problem,
            enabled=data.get("enabled", True),
            weight=Decimal(data["weight"]),
            points=Decimal(data["points"]),
            automated=some(data["automated"], ProblemGradingCategory.load),
            review=some(data["review"], ProblemGradingCategory.load),
            manual=some(data["manual"], ProblemGradingCategory.load),)

    def dump(self) -> dict:
        """Serialize with monad."""

        return dict(
            enabled=self.enabled,
            weight=str(self.weight),
            points=str(self.points),
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

    # Backlink
    assignment: "Assignment" = field(default=None)

    @classmethod
    def load(cls, data: dict, assignment: "Assignment" = None) -> "Problem":
        """Load directly from a dictionary."""

        self = cls(
            assignment=assignment,
            short=data["short"],
            title=data["title"],
            relative_path=Path(data["relative_path"]),
            grading=ProblemGrading.load(data["grading"]),
            authors=list(map(Author.load, data["authors"])),
            topics=data["topics"],
            notes=data.get("notes"),
            difficulty=data.get("difficulty"))
        self.grading.problem = self
        return self

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
class AssignmentDates(Model):
    """Assignment dates."""

    assigned: datetime.datetime
    due: datetime.datetime

    @classmethod
    def load(cls, data: dict) -> "AssignmentDates":
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
    assignment: "Assignment" = field(default=None)

    _weight: Decimal = field(init=False)

    @classmethod
    def load(cls, data: dict, assignment: "Assignment" = None) -> "AssignmentGrading":
        """Load from serialized."""

        return cls(points=data["points"], assignment=assignment)

    def weight(self) -> Decimal:
        """Compute cumulative weight of all problems."""

        try:
            return self._weight
        except AttributeError:
            self._weight = sum(problem.grading.weight for problem in self.assignment.problems)
            return self._weight

    def dump(self) -> dict:
        """Avoid recursion."""

        return dict(points=self.points)


@dataclass(eq=False)
class AssignmentMeta(Model):
    """Metadata about an assignment."""

    built: datetime.datetime = field(default_factory=datetime.datetime.now)
    curricula: str = version

    @classmethod
    def load(cls, data: dict) -> "AssignmentMeta":
        """Deserialize datetime."""

        return cls(
            built=parse_datetime(data["built"]),
            curricula=data["curricula"],)

    def dump(self) -> dict:
        """Serialize the datetime here too."""

        return dict(
            built=dump_datetime(self.built),
            curricula=version,)


@dataclass(eq=False)
class Assignment(Model):
    """Contains assignment metadata."""

    short: str
    title: str
    authors: List[Author]
    dates: AssignmentDates
    problems: List[Problem]
    grading: AssignmentGrading
    notes: Optional[str] = None
    meta: AssignmentMeta = AssignmentMeta()

    @classmethod
    def load(cls, data: dict, problems: List[Problem] = None) -> "Assignment":
        """Deserialize."""

        if problems is None:
            problems = list(map(Problem.load, data["problems"]))

        self = cls(
            short=data["short"],
            title=data["title"],
            authors=list(map(Author.load, data["authors"])),
            dates=AssignmentDates.load(data["dates"]),
            problems=problems,
            grading=AssignmentGrading.load(data["grading"]),
            notes=data.get("notes"),
            meta=AssignmentMeta.load(data["meta"]) if "meta" in data else AssignmentMeta())

        for problem in problems:
            problem.assignment = self
        self.grading.assignment = self

        return self

    def dump(self) -> dict:
        """Dump the assignment to JSON."""

        return dict(
            short=self.short,
            title=self.title,
            authors=[author.dump() for author in self.authors],
            dates=self.dates.dump(),
            problems=[problem.dump() for problem in self.problems],
            grading=self.grading.dump(),
            notes=self.notes,
            meta=self.meta.dump())
