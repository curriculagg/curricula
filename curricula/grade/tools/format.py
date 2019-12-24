import json
from typing import Dict, List
from pathlib import Path
from dataclasses import dataclass, field

from ...library.template import jinja2_create_environment
from ...shared import Files
from .. import root as grade_root


@dataclass
class ProblemSummary:
    tests_total: int = 0
    tests_correct: int = 0
    tests_incorrect: List[str] = field(default_factory=list)
    failed_setup: bool = False
    build_error: str = ""


@dataclass
class ReportSummary:
    problems: Dict[str, ProblemSummary] = field(default_factory=dict)


def summarize(grading_schema: dict, report: dict) -> ReportSummary:
    """Do a summary for a single student."""

    summary = ReportSummary()
    for problem_short, problem in grading_schema["problems"].items():
        problem_summary = summary.problems[problem_short] = ProblemSummary()
        for task_name, task in problem["tasks"].items():
            result = report[problem_short][task_name]
            if task["kind"] == "setup":
                if not result["complete"] or not result["passed"]:
                    problem_summary.failed_setup = True
                if "kind" in result and result["kind"] == "build" and not result["passed"] and "runtime" in result["details"]:
                    problem_summary.build_error = result["details"]["runtime"]["stderr"]
            elif task["kind"] == "test":
                problem_summary.tests_total += 1
                if result["complete"] and result["passed"]:
                    problem_summary.tests_correct += 1
                else:
                    problem_summary.tests_incorrect.append(task_name)
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
