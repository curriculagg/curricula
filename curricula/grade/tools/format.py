import json
from typing import Dict, List
from pathlib import Path
from dataclasses import dataclass, field

from ...template import jinja2_create_environment
from ...mapping.shared import Files


@dataclass
class ProblemSummary:
    problems_total: int = 0
    problems_correct: int = 0
    problems_incorrect: List[str] = field(default_factory=list)


@dataclass
class ReportSummary:
    problems: Dict[str, ProblemSummary] = field(default_factory=dict)
    failed_setup: bool = False


def summarize(grading_schema: dict, report: dict) -> ReportSummary:
    """Do a summary for a single student."""

    summary = ReportSummary()
    for problem_short, problem in grading_schema["problems"].items():
        problem_summary = summary.problems[problem_short] = ProblemSummary()
        for task_name, task in problem["tasks"].items():
            result = report[problem_short][task_name]
            if task["kind"] == "setup":
                summary.failed_setup = True
            elif task["kind"] == "test":
                problem_summary.problems_total += 1
                if result["complete"] and result["passed"]:
                    problem_summary.problems_correct += 1
                else:
                    problem_summary.problems_incorrect.append(task_name)
    return summary


def format_report_markdown(grading_path: Path, report_path: Path) -> str:
    """Return a formatted markdown report."""

    environment = jinja2_create_environment(custom_template_path=grading_path)
    with grading_path.joinpath(Files.GRADING).open() as file:
        grading_schema = json.load(file)
    with report_path.open() as file:
        report = json.load(file)
    summary = summarize(grading_schema, report)

    environment.globals.update(schema=grading_schema, summary=summary)
    report_template = environment.get_template("template/grading/report.md")
    return report_template.render()
