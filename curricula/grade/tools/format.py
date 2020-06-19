import json
from typing import Dict, Iterable, Iterator
from pathlib import Path
from dataclasses import dataclass, field
from decimal import Decimal

from ..task import Result
from ..models import GradingAssignment, GradingProblem
from ..report import AssignmentReport, ProblemReport
from ...library.template import jinja2_create_environment, DEFAULT_TEMPLATE_PATH, pretty


def sum_weights(results: Iterable[Result]) -> Decimal:
    return sum(Decimal(str(result.task.details.get("weight", "1"))) for result in results)


@dataclass(eq=False)
class ProblemSummary:
    """A summary of the results from a problem's cases."""

    problem: GradingProblem
    report: ProblemReport

    # Main tests
    test_results_count: int = 0
    test_results_passing_count: int = 0
    test_results_failing_count: int = 0

    def __post_init__(self):
        """Cache some common analysis of the data."""

        for task in self.problem.grader.tasks:
            if task.stage == "test":
                self.test_results_count += 1

                # Increment counts
                result = self.report[task.name]
                if result.passing and result.complete:
                    self.test_results_passing_count += 1
                else:
                    self.test_results_failing_count += 1

    @property
    def test_results_passing(self) -> Iterator[Result]:
        """Count the number of tests that passed."""

        for task in self.problem.grader.tasks:
            if task.stage == "test":
                result = self.report[task.name]
                if result.passing and result.complete:
                    yield result

    @property
    def test_results_failing(self) -> Iterator[Result]:
        """Count the number of tests that passed."""

        for task in self.problem.grader.tasks:
            if task.stage == "test":
                result = self.report[task.name]
                if not result.passing or not result.complete:
                    yield result

    @property
    def tests_fraction(self) -> str:
        """Format a fraction."""

        numerator = sum_weights(self.test_results_passing)
        denominator = numerator + sum_weights(self.test_results_failing)
        if denominator == 0:
            return f"0/0"
        points_automated = self.problem.grading.points_automated
        if denominator != points_automated:
            numerator = numerator / denominator * points_automated
            denominator = points_automated
        return f"{pretty(numerator)}/{pretty(denominator)}"

    @property
    def tests_percentage(self) -> Decimal:
        """Compute the percentage."""

        if self.test_results_count == 0:
            return Decimal("0")
        numerator = sum_weights(self.test_results_passing)
        denominator = numerator + sum_weights(self.test_results_failing)
        return Decimal(numerator) / Decimal(denominator)


@dataclass(eq=False)
class ReportSummary:
    """Summary of problems."""

    problems: Dict[str, ProblemSummary] = field(default_factory=dict)


def summarize(assignment: GradingAssignment, report: AssignmentReport) -> ReportSummary:
    """Do a summary for a single student."""

    summary = ReportSummary()
    for problem in assignment.problems:
        if problem.grading.is_automated:
            summary.problems[problem.short] = ProblemSummary(problem, report[problem.short])

    return summary


def format_report_markdown(grading_path: Path, report_path: Path, template_path: Path = None) -> str:
    """Return a formatted markdown report."""

    if template_path is None:
        template_path = DEFAULT_TEMPLATE_PATH

    environment = jinja2_create_environment(template=template_path)
    assignment = GradingAssignment.read(grading_path)
    with report_path.open() as file:
        report = AssignmentReport.load(json.load(file), assignment)
    summary = summarize(assignment, report)

    environment.globals.update(assignment=assignment, summary=summary)
    report_template = environment.get_template("template:grade/report/assignment.md")
    return report_template.render() + "\n"
