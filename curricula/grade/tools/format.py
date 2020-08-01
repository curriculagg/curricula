import jinja2

import json
from typing import Dict, Iterable, Iterator, List
from pathlib import Path
from dataclasses import dataclass, field
from decimal import Decimal

from ..task import Result
from ..models import GradingAssignment, GradingProblem
from ..report import AssignmentReport, ProblemReport
from ...library.template import jinja2_create_environment, DEFAULT_TEMPLATE_PATH, pretty


def sum_weights(results: Iterable[Result]) -> Decimal:
    return sum(result.task.weight for result in results)


@dataclass(eq=False)
class ProblemSummary:
    """A summary of the results from a problem's cases."""

    problem: GradingProblem
    report: ProblemReport

    # Setup issues
    setup_results_errored: List[Result] = field(default_factory=list)

    # Main tests
    test_results_count: int = 0
    test_results_passing_count: int = 0

    # Weight
    test_results_passing_weight: Decimal = Decimal(0)

    def __post_init__(self):
        """Cache some common analysis of the data."""

        for task in self.problem.grader.tasks:
            result = self.report[task.name]

            if task.stage == "setup":
                if result.error is not None:
                    self.setup_results_errored.append(result)

            if task.stage == "test":
                self.test_results_count += 1

                # Increment counts
                if result.passing and result.complete:
                    self.test_results_passing_count += 1
                    self.test_results_passing_weight += task.weight

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
    def passing_fraction(self) -> str:
        return f"{self.test_results_passing_count}/{self.test_results_count}"

    @property
    def points_fraction(self) -> str:
        """Format a fraction."""

        numerator = self.test_results_passing_weight
        denominator = self.problem.grader.test.weight
        if denominator == 0:
            return f"0/0"

        points_total_automated = self.problem.grading.automated.points
        if denominator != points_total_automated:
            numerator = numerator / denominator * points_total_automated
            denominator = points_total_automated
        return f"{pretty(numerator)}/{pretty(denominator)}"

    @property
    def points_percentage(self) -> Decimal:
        """Compute the percentage."""

        if self.test_results_count == 0:
            return Decimal("0")

        numerator = self.test_results_passing_weight
        denominator = self.problem.grader.test.weight
        if denominator == 0:
            return Decimal("0")

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


def create_format_environment(custom_template_path: Path = None) -> jinja2.Environment:
    """Create the requisite environment."""

    if custom_template_path is None:
        custom_template_path = DEFAULT_TEMPLATE_PATH
    return jinja2_create_environment(custom_template_path=custom_template_path)


def format_report_markdown(
        assignment: GradingAssignment,
        report_path: Path,
        environment: jinja2.Environment = None,
        options: dict = None) -> str:
    """Return a formatted markdown report."""

    with report_path.open() as file:
        report = AssignmentReport.load(json.load(file), assignment)
    if report.partial:
        return "Cannot format a partial report!"

    summary = summarize(assignment, report)
    if environment is None:
        environment = create_format_environment()

    environment.globals.update(assignment=assignment, summary=summary, options=options)
    report_template = environment.get_template("template:grade/report/assignment.md")
    return report_template.render() + "\n"
