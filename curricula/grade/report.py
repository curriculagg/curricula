from __future__ import annotations

from typing import List, Dict, Iterable
from dataclasses import dataclass, field

from .resource import Resource
from .task import Task, Result

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

    results: List[Result] = field(default_factory=list)
    lookup: Dict[str, Result] = field(default_factory=dict, init=False)

    def __post_init__(self):
        """Populate lookup if initialized with results."""

        for result in self.results:
            self.lookup[result.task.name] = result

    def __getitem__(self, item: str) -> Result:
        """Look up a result by task name."""

        return self.lookup[item]

    def add(self, result: Result):
        """Add a result to the report.

        If we hide a result, it will not be serialized into the final report.
        This is useful for when we don't want someone who's looking at the
        report to know about some subset of the tests.
        """

        self.lookup[result.task.name] = result
        self.results.append(result)

    def dump(self) -> dict:
        """Dump the result to a serializable format."""

        return {result.task.name: result.dump() for result in self.results}

    @classmethod
    def load(cls, data: dict, tasks: Iterable[Task]) -> "ProblemReport":
        """Deserialize, rebinding to provided tasks."""

        return ProblemReport([Result.load(data[task.name], task) for task in tasks])

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
class AssignmentReport:
    """Aggregation of problem reports."""

    reports: Dict[str, ProblemReport] = field(default_factory=dict)

    def __getitem__(self, item: str) -> ProblemReport:
        """Index problem reports by problem short."""

        return self.reports[item]

    def __setitem__(self, key: str, value: ProblemReport):
        """Set the result from a problem."""

        self.reports[key] = value

    def dump(self) -> dict:
        """Serialize as dictionary to shorten rebuild."""

        return {problem_short: problem_report.dump() for problem_short, problem_report in self.reports.items()}

    @classmethod
    def load(cls, data: dict, assignment: "GradingAssignment") -> "AssignmentReport":
        """Deserialize and bind to existing tasks."""

        reports = {}
        for problem in assignment.problems:
            if problem.grading.is_automated:
                reports[problem.short] = ProblemReport.load(data[problem.short], problem.grader.tasks)

        return AssignmentReport(reports)
