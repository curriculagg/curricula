import time
import datetime

from decimal import Decimal
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Callable, TypeVar
from abc import ABC, abstractmethod
from functools import lru_cache

from .version import version

TZ = datetime.timezone(offset=datetime.timedelta(seconds=time.timezone))


def deserialize_datetime(s: str) -> Optional[datetime.datetime]:
    """Deserialize our standard format."""

    if s is None:
        return None
    return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=TZ)


def serialize_datetime(d: datetime) -> Optional[str]:
    """Serialize back."""

    if d is None:
        return None
    return d.strftime("%Y-%m-%d %H:%M:%S")


T = TypeVar("T")
U = TypeVar("U")


def some(value: Optional[T], method: Callable[[T], U]) -> Optional[U]:
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

    weight: Decimal
    points: Decimal

    # Whether it should be used
    enabled: bool = True

    # Intrinsic
    name: Optional[str] = None
    minutes: Optional[float] = None

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


@dataclass(eq=False)
class ProblemGrading(Model):
    """Data for each grading method."""

    weight: Decimal = Decimal(0)
    points: Decimal = Decimal(0)

    enabled: bool = True

    automated: Optional[ProblemGradingCategory] = None
    review: Optional[ProblemGradingCategory] = None
    manual: Optional[ProblemGradingCategory] = None

    @property
    def is_automated(self) -> bool:
        return self.enabled and self.automated is not None and self.automated.enabled

    @property
    def is_review(self) -> bool:
        return self.enabled and self.review is not None and self.review.enabled

    @property
    def is_manual(self) -> bool:
        return self.enabled and self.manual is not None and self.manual.enabled

    @property
    @lru_cache(maxsize=1)
    def weight_total(self) -> Decimal:
        return sum((
            self.automated.weight if self.automated and self.automated.enabled else 0,
            self.review.weight if self.review and self.review.enabled else 0,
            self.manual.weight if self.manual and self.manual.enabled else 0))

    @property
    def percentage_automated(self) -> Decimal:
        return self.automated.weight / self.weight_total

    @property
    def percentage_review(self) -> Decimal:
        return self.review.weight / self.weight_total

    @property
    def percentage_manual(self) -> Decimal:
        return self.manual.weight / self.weight_total

    @classmethod
    def load(cls, data: dict) -> "ProblemGrading":
        """Deserialize each method."""

        if data["automated"] is not None and data["automated"].get("name") is None:
            data["automated"]["name"] = "Automated tests"
        if data["review"] is not None and data["review"].get("name") is None:
            data["review"]["name"] = "Code review"
        if data["manual"] is not None and data["manual"].get("name") is None:
            data["manual"]["name"] = "Manual grading"

        return cls(
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

    # Defined in assignment reference
    grading: ProblemGrading = field(default_factory=ProblemGrading)

    # Most specific directory containing relevant files relative to assignment root
    relative_path: Path = field(default_factory=Path)

    # Intrinsic
    authors: List[Author] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    difficulty: Optional[str] = None

    # Backlink
    assignment: "Assignment" = None

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
class AssignmentGrading(Model):
    """Weights and points."""

    points: int
    assignment: "Assignment" = field(default=None)

    @classmethod
    def load(cls, data: dict, assignment: "Assignment" = None) -> "AssignmentGrading":
        """Load from serialized."""

        return cls(points=data["points"], assignment=assignment)

    @lru_cache(maxsize=1)
    def weight(self) -> Decimal:
        """Compute cumulative weight of all problems."""

        return sum(problem.grading.weight for problem in self.assignment.problems)

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
            built=deserialize_datetime(data["built"]),
            curricula=data["curricula"],)

    def dump(self) -> dict:
        """Serialize the datetime here too."""

        return dict(
            built=serialize_datetime(self.built),
            curricula=version,)


@dataclass(eq=False)
class AssignmentDates(Model):
    """Assignment dates."""

    assigned: datetime.datetime
    due: Optional[datetime.datetime]
    deadline: Optional[datetime.datetime]

    @classmethod
    def load(cls, data: dict) -> "AssignmentDates":
        """Convert to datetime."""

        return cls(
            assigned=deserialize_datetime(data["assigned"]),
            due=deserialize_datetime(data.get("due")),
            deadline=deserialize_datetime(data.get("deadline")))

    def dump(self) -> dict:
        """Specifically serialize the datetime."""

        return dict(
            assigned=serialize_datetime(self.assigned),
            due=serialize_datetime(self.due),
            deadline=serialize_datetime(self.deadline))


@dataclass(eq=False)
class Assignment(Model):
    """Contains assignment metadata."""

    short: str
    title: str
    authors: List[Author]

    problems: List[Problem]
    grading: AssignmentGrading

    dates: Optional[AssignmentDates] = None

    notes: Optional[str] = None
    meta: AssignmentMeta = AssignmentMeta()
    extra: Optional[dict] = None

    @classmethod
    def load(cls, data: dict, problems: List[Problem] = None) -> "Assignment":
        """Deserialize."""

        if problems is None:
            problems = list(map(Problem.load, data["problems"]))

        self = cls(
            short=data["short"],
            title=data["title"],
            authors=list(map(Author.load, data["authors"])),
            problems=problems,
            grading=AssignmentGrading.load(data["grading"]),
            dates=AssignmentDates.load(data["dates"]),
            extra=data.get("extra"),
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
            problems=[problem.dump() for problem in self.problems],
            grading=self.grading.dump(),
            dates=self.dates.dump() if self.dates is not None else None,
            extra=self.extra,
            notes=self.notes,
            meta=self.meta.dump())
