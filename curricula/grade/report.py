from typing import List, Dict
from dataclasses import dataclass, field

from .resource import Resource
from .task import Result


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

    lookup: Dict[str, Result] = field(default_factory=dict)
    results: List[Result] = field(default_factory=list)

    def check(self, task_name: str) -> bool:
        """Check the result of a task."""

        result = self.lookup[task_name]
        return result.complete and result.passed

    def add(self, result: Result, hidden: bool = False):
        """Add a result to the report."""

        self.lookup[result.task.name] = result
        if not hidden:
            self.results.append(result)

    def dump(self) -> dict:
        """Dump the result to a serializable format."""

        return {result.task.name: result.dump() for result in self.results}

    def statistics(self) -> ProblemReportStatistics:
        """Run the numbers."""

        statistics = ProblemReportStatistics()
        for result in self.results:
            statistics.tasks_total += 1
            if result.complete:
                statistics.tasks_complete += 1
            if result.passed:
                statistics.tasks_passed += 1
            if result.task.stage == "test":
                statistics.tests_total += 1
                if result.complete:
                    statistics.tests_complete += 1
                if result.passed:
                    statistics.tests_passed += 1
        return statistics


class AssignmentReport(dict):
    """Aggregation of problem reports."""

    def dump(self) -> dict:
        return {problem_short: problem_report.dump() for problem_short, problem_report in self.items()}
