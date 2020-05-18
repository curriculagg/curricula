import json
from typing import Dict, Iterable, Iterator
from pathlib import Path
from dataclasses import dataclass, field
from decimal import Decimal

from ..task import Task, Result
from ..models import GradingAssignment, GradingProblem
from ..report import AssignmentReport, ProblemReport
from ...library.template import jinja2_create_environment, DEFAULT_TEMPLATE_PATH


def sum_weights(results: Iterable[Result]) -> float:
    return sum(Decimal(str(result.task.details.get("weight", "1"))) for result in results)


@dataclass(eq=False)
class ProblemSummary:
    """A summary of the results from a problem's cases."""

    problem: GradingProblem
    report: ProblemReport

    # Main tests
    tests_count: int = 0
    tests_passing_count: int = field(init=False)
    tests_failing_count: int = field(init=False)

    def __post_init__(self):
        """Cache some common analysis of the data."""

        for task in self.problem.grader.tasks:
            if task.stage == "test":
                self.tests_count += 1

                # Increment counts
                result = self.report[task.name]
                if result.passing and result.complete:
                    self.tests_passing_count += 1
                else:
                    self.tests_failing_count += 1

    @property
    def tests_passing(self) -> Iterator[Result]:
        """Count the number of tests that passed."""

        for task in self.problem.grader.tasks:
            if task.stage == "test":
                result = self.report[task.name]
                if result.passing and result.complete:
                    yield result

    @property
    def tests_failing(self) -> Iterator[Result]:
        """Count the number of tests that passed."""

        for task in self.problem.grader.tasks:
            if task.stage == "test":
                result = self.report[task.name]
                if not result.passing or not result.complete:
                    yield result

    @property
    def tests_fraction(self) -> str:
        """Format a fraction."""

        numerator = sum_weights(self.tests_passing)
        denominator = numerator + sum_weights(self.tests_failing)
        return f"{numerator}/{denominator}"

    @property
    def tests_percentage(self) -> Decimal:
        """Compute the percentage."""

        if self.tests_count == 0:
            return Decimal("0")
        numerator = sum_weights(self.tests_passing)
        denominator = numerator + sum_weights(self.tests_failing)
        return Decimal(numerator) / Decimal(denominator)


@dataclass(eq=False)
class ReportSummary:
    """Summary of problems."""

    problems: Dict[str, ProblemSummary] = field(default_factory=dict)


def summarize(assignment: GradingAssignment, report: AssignmentReport) -> ReportSummary:
    """Do a summary for a single student."""

    summary = ReportSummary()
    for problem in assignment.problems:
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
