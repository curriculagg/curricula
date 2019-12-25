import json
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass, field

from .. import root as grade_root
from ..task import Task
from ...library.template import jinja2_create_environment
from ...shared import Files


@dataclass(eq=False)
class ProblemSummary:
    """A summary of the results from a problem's cases."""

    # Main tests
    tests_total: int = 0
    tests_correct: List[Task] = field(default_factory=list)
    tests_incorrect: List[Task] = field(default_factory=list)

    # Setup problems
    setup_failed: bool = False
    setup_error: Optional[str] = None

    @property
    def tests_percentage(self):
        """Compute the percentage."""

        if self.tests_total == 0:
            return 1
        return len(self.tests_correct) / self.tests_total


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
                    problem_summary.setup_error = result["details"]["error"]

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

    environment = jinja2_create_environment(grade_root)
    with grading_path.joinpath(Files.GRADING).open() as file:
        grading_schema = json.load(file)
    with report_path.open() as file:
        report = json.load(file)
    summary = summarize(grading_schema, report)

    environment.globals.update(schema=grading_schema, summary=summary)
    report_template = environment.from_string(template_path.read_text())
    return report_template.render() + "\n"
