from __future__ import annotations

import datetime
from typing import List, Dict, Iterable, Optional
from dataclasses import dataclass, field

from .resource import Resource
from .task import Task, Result
from ..models import serialize_datetime

import typing

if typing.TYPE_CHECKING:
    from .models import GradingAssignment


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
class ProblemReport(Resource):
    """The final report returned by the testing framework."""

    partial: bool = field(default=False)
    results: List[Result] = field(default_factory=list)
    lookup: Dict[str, Result] = field(default_factory=dict, init=False)

    def __post_init__(self):
        """Populate lookup if initialized with results."""

        for result in self.results:
            self.lookup[result.task.name] = result

    def __getitem__(self, item: str) -> Result:
        """Look up a result by task name."""

        return self.lookup[item]

    def get(self, item: str) -> Optional[Result]:
        """Mimic lookup get."""

        return self.lookup.get(item)

    def add(self, result: Result):
        """Add a result to the report.

        If we hide a result, it will not be serialized into the final report.
        This is useful for when we don't want someone who's looking at the
        report to know about some subset of the tests.
        """

        self.results.append(result)
        self.lookup[result.task.name] = result

    def dump(self) -> dict:
        """Dump the result to a serializable format."""

        return {result.task.name: result.dump() for result in self.results}

    @classmethod
    def load(cls, data: dict, tasks: Iterable[Task]) -> "ProblemReport":
        """Deserialize, rebinding to provided tasks."""

        report = ProblemReport()
        for task in tasks:
            result_data = data.get(task.name)
            if result_data is not None:
                report.add(Result.load(result_data, task))
            else:
                report.partial = True
        return report

    def statistics(self) -> ProblemReportStatistics:
        """Run the numbers."""

        statistics = ProblemReportStatistics()
        for result in self.results:
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
class AssignmentReportMetaAssignment:
    """Structured data about the origin assignment."""

    short: str
    # hash: str

    @classmethod
    def create(cls, assigment: GradingAssignment) -> "AssignmentReportMetaAssignment":
        return AssignmentReportMetaAssignment(short=assigment.short)

    @classmethod
    def load(cls, data: dict):
        return AssignmentReportMetaAssignment(**data)

    def dump(self) -> dict:
        return dict(short=self.short)


@dataclass(eq=False)
class AssignmentReportMeta:
    """Metadata associated with a assignment report."""

    assignment: AssignmentReportMetaAssignment
    timestamp: datetime.datetime
    partial: bool

    @classmethod
    def create(cls, assigment: GradingAssignment, partial: bool = False) -> "AssignmentReportMeta":
        return AssignmentReportMeta(
            assignment=AssignmentReportMetaAssignment(short=assigment.short),
            timestamp=datetime.datetime.now(),
            partial=partial)

    @classmethod
    def load(cls, data: dict):
        assignment = AssignmentReportMetaAssignment.load(data.pop("assignment"))
        return AssignmentReportMeta(assignment=assignment, **data)

    def dump(self) -> dict:
        return dict(
            assignment=self.assignment.dump(),
            timestamp=serialize_datetime(self.timestamp),
            partial=self.partial)


@dataclass(eq=False)
class AssignmentReport:
    """Aggregation of problem reports."""

    meta: AssignmentReportMeta
    problems: Dict[str, ProblemReport] = field(default_factory=dict)

    def __getitem__(self, item: str) -> ProblemReport:
        """Index problem reports by problem short."""

        return self.problems[item]

    def __setitem__(self, key: str, value: ProblemReport):
        """Set the result from a problem."""

        self.problems[key] = value
        self.meta.partial = self.meta.partial or value.partial

    def dump(self) -> dict:
        """Serialize as dictionary to shorten rebuild."""

        problems = {problem_short: problem_report.dump() for problem_short, problem_report in self.problems.items()}
        return dict(problems=problems, meta=self.meta.dump())

    @classmethod
    def create(cls, assigment: "GradingAssignment") -> "AssignmentReport":
        """Create from assignment for metadata."""

        return AssignmentReport(meta=AssignmentReportMeta.create(assigment))

    @classmethod
    def load(cls, data: dict, assignment: "GradingAssignment") -> "AssignmentReport":
        """Deserialize and bind to existing tasks."""

        meta = AssignmentReportMeta.load(data["meta"])
        report = AssignmentReport(meta=meta)

        for problem in assignment.problems:
            if problem.grading.is_automated:
                report[problem.short] = ProblemReport.load(data["problems"][problem.short], problem.grader.tasks)

        return report
