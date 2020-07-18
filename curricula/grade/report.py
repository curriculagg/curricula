from __future__ import annotations

import datetime
from typing import Dict, Optional
from dataclasses import dataclass, field

from .task import Result
from ..models import serialize_datetime, deserialize_datetime

import typing

if typing.TYPE_CHECKING:
    from .models import GradingAssignment, GradingProblem


@dataclass(eq=False)
class ProblemReportStatistics:
    """Rudimentary sums from the report results."""

    tasks_total: int = 0
    tasks_complete: int = 0
    tasks_passed: int = 0
    tests_total: int = 0
    tests_complete: int = 0
    tests_passed: int = 0

    def __str__(self) -> str:
        """Format nicely."""

        tasks_percentage = round(self.tasks_complete/(self.tasks_complete or 1) * 100, 2)
        tests_percentage = round(self.tests_passed/(self.tests_complete or 1) * 100, 2)
        return (f"{self.tasks_complete}/{self.tasks_complete} tasks complete ({tasks_percentage}%), "
                f"{self.tests_passed}/{self.tests_total} tests passed ({tests_percentage}%)")


@dataclass(eq=False)
class ProblemReportProblemReference:
    """Reference to original problem."""

    short: str

    def dump(self) -> dict:
        return dict(short=self.short)

    @classmethod
    def create(cls, problem: "GradingProblem") -> "ProblemReportProblemReference":
        return ProblemReportProblemReference(short=problem.short)

    @classmethod
    def load(cls, data: dict) -> "ProblemReportProblemReference":
        return ProblemReportProblemReference(**data)


@dataclass(eq=False)
class ProblemReport:
    """The final report returned by the testing framework."""

    problem: ProblemReportProblemReference
    results: Dict[str, Result] = field(default_factory=dict)
    partial: bool = True

    def __getitem__(self, item: str) -> Result:
        """Look up a result by task name."""

        return self.results[item]

    def get(self, item: str) -> Optional[Result]:
        """Mimic lookup get."""

        return self.results.get(item)

    def add(self, result: Result):
        """Add a result to the report."""

        self.results[result.task.name] = result

    def dump(self) -> dict:
        """Dump the result to a serializable format."""

        results = {result.task.name: result.dump() for result in self.results.values()}
        return dict(problem=self.problem.dump(), results=results, partial=self.partial)

    @classmethod
    def create(cls, problem: GradingProblem) -> "ProblemReport":
        """Create a new problem."""

        return ProblemReport(problem=ProblemReportProblemReference.create(problem))

    @classmethod
    def load(cls, data: dict, problem: GradingProblem) -> "ProblemReport":
        """Deserialize, rebinding to provided tasks."""

        partial = data["partial"]
        results = {}
        for task in problem.grader.tasks:
            result_data = data["results"].get(task.name)
            if result_data is not None:
                results[task.name] = Result.load(result_data, task)
            else:
                partial = True

        return ProblemReport(
            problem=ProblemReportProblemReference.load(data["problem"]),
            results=results,
            partial=partial)

    def statistics(self) -> ProblemReportStatistics:
        """Run the numbers."""

        statistics = ProblemReportStatistics()
        for result in self.results.values():
            statistics.tasks_total += 1
            if result.complete:
                statistics.tasks_complete += 1
            if result.passing:
                statistics.tasks_passed += 1
            if result.task.stage == "test":
                statistics.tests_total += 1
                if result.complete:
                    statistics.tests_complete += 1
                if result.passing:
                    statistics.tests_passed += 1
        return statistics


@dataclass(eq=False)
class AssignmentReportAssignmentReference:
    """Structured data about the origin assignment."""

    short: str
    # hash: str

    def dump(self) -> dict:
        return dict(short=self.short)

    @classmethod
    def create(cls, assignment: GradingAssignment) -> "AssignmentReportAssignmentReference":
        return AssignmentReportAssignmentReference(short=assignment.short)

    @classmethod
    def load(cls, data: dict):
        return AssignmentReportAssignmentReference(**data)


@dataclass(eq=False)
class AssignmentReport:
    """Aggregation of problem reports."""

    assignment: AssignmentReportAssignmentReference
    problems: Dict[str, ProblemReport] = field(default_factory=dict)
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    partial: bool = False

    def __post_init__(self):
        """Check if any initialized problems are partial."""

        for problem in self.problems.values():
            if problem.partial:
                self.partial = True
                break

    def __getitem__(self, item: str) -> ProblemReport:
        """Index problem reports by problem short."""

        return self.problems[item]

    def __setitem__(self, key: str, value: ProblemReport):
        """Set the result from a problem."""

        self.problems[key] = value
        self.partial = self.partial or value.partial

    def dump(self) -> dict:
        """Serialize as dictionary to shorten rebuild."""

        problems = {problem_short: problem_report.dump() for problem_short, problem_report in self.problems.items()}
        return dict(
            assignment=self.assignment.dump(),
            problems=problems,
            timestamp=serialize_datetime(self.timestamp),
            partial=self.partial)

    @classmethod
    def create(cls, assigment: "GradingAssignment") -> "AssignmentReport":
        """Create from assignment for metadata."""

        return AssignmentReport(assignment=AssignmentReportAssignmentReference.create(assigment))

    @classmethod
    def load(cls, data: dict, assignment: "GradingAssignment") -> "AssignmentReport":
        """Deserialize and bind to existing tasks."""

        assignment_reference = AssignmentReportAssignmentReference.load(data.pop("assignment"))
        timestamp = deserialize_datetime(data.pop("timestamp"))

        problems = {}
        for problem in assignment.problems:
            if problem.grading.is_automated:
                problems[problem.short] = ProblemReport.load(data["problems"][problem.short], problem)

        return AssignmentReport(
            assignment=assignment_reference,
            problems=problems,
            timestamp=timestamp,
            partial=data["partial"])
