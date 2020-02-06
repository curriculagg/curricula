import json
from typing import Dict, List, Optional, Iterable
from pathlib import Path
from dataclasses import dataclass, field
from decimal import Decimal

from ...library.template import jinja2_create_environment
from ...shared import Files


def sum_weights(tasks: Iterable[dict]) -> float:
    return sum(Decimal(str(task["details"].get("weight", "1"))) for task in tasks)


@dataclass(eq=False)
class ProblemSummary:
    """A summary of the results from a problem's cases."""

    # Main tests
    tests_total: int = 0
    tests_correct: List[dict] = field(default_factory=list)
    tests_incorrect: List[dict] = field(default_factory=list)

    # Setup problems
    setup_failed: bool = False
    setup_failed_task: Optional[str] = None
    setup_error: Optional[str] = None

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


def summarize(grading_schema: dict, report: dict) -> ReportSummary:
    """Do a summary for a single student."""

    summary = ReportSummary()
    for problem_short, problem in grading_schema["problems"].items():
        problem_summary = summary.problems[problem_short] = ProblemSummary()
        for task_name, task in problem["tasks"].items():
            result = report[problem_short][task_name]

            # Diagnose any issues in setup
            if task["stage"] == "setup":
                if not result["complete"] or not result["passed"]:
                    problem_summary.setup_failed = True
                    problem_summary.setup_failed_task = task_name
                    if "error" in result["details"]:
                        problem_summary.setup_error = result["details"]["error"]
                    elif "runtime" in result["details"]:
                        problem_summary.setup_error = result["details"]["runtime"]["stderr"]

            # Problem summary
            elif task["stage"] == "test":
                problem_summary.tests_total += 1
                if result["complete"] and result["passed"]:
                    problem_summary.tests_correct.append(task)
                else:
                    problem_summary.tests_incorrect.append(task)

    return summary


def format_report_markdown(grading_path: Path, template_path: Path, report_path: Path) -> str:
    """Return a formatted markdown report."""

    environment = jinja2_create_environment()
    with grading_path.joinpath(Files.GRADING).open() as file:
        grading_schema = json.load(file)
    with report_path.open() as file:
        report = json.load(file)
    summary = summarize(grading_schema, report)

    environment.globals.update(schema=grading_schema, summary=summary)
    report_template = environment.from_string(template_path.read_text())
    return report_template.render() + "\n"
