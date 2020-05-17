import json
from typing import Dict, List, Optional, Iterable
from pathlib import Path
from dataclasses import dataclass, field
from decimal import Decimal

from ..models import GradingAssignment, GradingProblem
from ..task import Task
from ...library.template import jinja2_create_environment, DEFAULT_TEMPLATE_PATH


def sum_weights(tasks: Iterable[Task]) -> float:
    return sum(Decimal(str(task.details.get("weight", "1"))) for task in tasks)


@dataclass(eq=False)
class ProblemSummary:
    """A summary of the results from a problem's cases."""

    problem: GradingProblem

    # Main tests
    tests_total: int = 0
    tests_correct: List[Task] = field(default_factory=list)
    tests_incorrect: List[Task] = field(default_factory=list)

    # Setup problems
    setup_failed: bool = False
    setup_failed_task: Optional[str] = None
    setup_error_description: Optional[str] = None
    setup_error_traceback: Optional[str] = None

    @property
    def tests_fraction(self) -> str:
        """Format a fraction."""

        numerator = sum_weights(self.tests_correct)
        denominator = numerator + sum_weights(self.tests_incorrect)
        return f"{numerator}/{denominator}"

    @property
    def tests_percentage(self) -> Decimal:
        """Compute the percentage."""

        if self.tests_total == 0:
            return Decimal("0")
        numerator = sum_weights(self.tests_correct)
        denominator = numerator + sum_weights(self.tests_incorrect)
        return Decimal(numerator) / Decimal(denominator)


@dataclass(eq=False)
class ReportSummary:
    """Summary of problems."""

    problems: Dict[str, ProblemSummary] = field(default_factory=dict)


def summarize(assignment: GradingAssignment, report: dict) -> ReportSummary:
    """Do a summary for a single student."""

    summary = ReportSummary()
    for problem in assignment.problems:
        problem_summary = summary.problems[problem.short] = ProblemSummary(problem)
        for task in problem.grader.tasks:
            result = report[problem.short][task.name]

            # Diagnose any issues in setup
            if task.stage == "setup":
                if not result["complete"] or not result["passing"]:
                    problem_summary.setup_failed = True
                    problem_summary.setup_failed_task = task.name
                    if "error" in result["details"]:
                        problem_summary.setup_error_description = result["details"]["error"]["description"]
                    elif "runtime" in result["details"]:
                        problem_summary.setup_error_traceback = result["details"]["runtime"]["stderr"]

            # Problem summary
            elif task.stage == "test":
                problem_summary.tests_total += 1
                if result["complete"] and result["passing"]:
                    problem_summary.tests_correct.append(task)
                else:
                    problem_summary.tests_incorrect.append(task)

    return summary


def format_report_markdown(grading_path: Path, report_path: Path, template_path: Path = None) -> str:
    """Return a formatted markdown report."""

    if template_path is None:
        template_path = DEFAULT_TEMPLATE_PATH

    environment = jinja2_create_environment(template=template_path)
    assignment = GradingAssignment.read(grading_path)
    with report_path.open() as file:
        report = json.load(file)
    summary = summarize(assignment, report)

    environment.globals.update(assignment=assignment, summary=summary)
    report_template = environment.get_template("template:grade/report/assignment.md")
    return report_template.render() + "\n"
