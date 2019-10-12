import json
import statistics
from typing import List, Dict
from dataclasses import dataclass, field
from pathlib import Path

from ...mapping.shared import Files


@dataclass
class TaskSummary:
    """Statistics about task results."""

    task: dict
    students_complete: List["StudentSummary"] = field(default_factory=list)
    students_passed: List["StudentSummary"] = field(default_factory=list)


@dataclass
class StudentSummary:
    """Statistics for an individual student."""

    student: dict
    tasks_complete: List[TaskSummary] = field(default_factory=list)
    tasks_passed: List[TaskSummary] = field(default_factory=list)


@dataclass
class ProblemSummary:
    """Statistics about a set of tests."""

    tasks: List[TaskSummary] = field(default_factory=list)
    students: List[StudentSummary] = field(default_factory=list)


def build_problem_summary(problem_grading_schema: dict, reports_directory: Path) -> ProblemSummary:
    """Build a table of results with axes students and tasks."""

    summary = ProblemSummary()
    tasks = problem_grading_schema["tasks"]

    for report_path in reports_directory.glob("*.json"):
        with report_path.open() as file:
            report = json.load(file)
        report_name = report_path.parts[-1].rsplit(".")[0]

        student_summary = StudentSummary(dict(username=report_name))
        summary.students.append(student_summary)

        for result in report:
            task_name = result["task"]
            task = tasks[task_name]

            if task["kind"] == "setup" and not result["passed"]:
                error = result["details"]["error"] if "error" in result["details"] else ""
                print("{} failed {}: {}".format(student_summary.student["username"], result["task"]["name"], error))

            if result["complete"]:
                task.students_complete.append(student_summary)
                student_summary.tasks_complete.append(task)
            if result["passed"]:
                task.students_passed.append(student_summary)
                student_summary.tasks_passed.append(task)

    return summary


def build_summary(grading_schema: dict, reports_directory: Path) -> Dict[str, ProblemSummary]:
    """Compile problem summaries."""

    result = {}
    for key, problem_grading_schema in grading_schema.items():
        result[key] = build_problem_summary(problem_grading_schema, reports_directory)
    return result


def percent(x, n) -> str:
    return f"{round(x / n * 1000) / 10}%"


def filter_tests(tasks: List[TaskSummary]) -> List[TaskSummary]:
    return list(task_summary for task_summary in tasks if task_summary.task["kind"] == "test")


def summarize(grading_path: Path, reports_path: Path):
    """Do summaries of the reports in a directory."""

    with grading_path.joinpath(Files.GRADING).open() as file:
        grading_schema = json.load(file)

    summary = build_summary(grading_schema, reports_path)

    for problem_short, problem_summary in summary.items():
        print(problem_short)
        for task_summary in problem_summary.tasks:
            task_name = task_summary.task["name"]
            print(f"{task_name}: {percent(len(task_summary.students_passed), len(task_summary.students_complete))}")

    print()

    for problem_short, problem_summary in summary.items():
        print(problem_short)
        scores = []

        for student_summary in problem_summary.students:
            count_tests_complete = len(filter_tests(student_summary.tasks_complete))
            if count_tests_complete:
                scores.append(len(filter_tests(student_summary.tasks_passed)) / count_tests_complete)

        print(len(scores))
        print(statistics.mean(scores) * 100)
        print(statistics.median(scores) * 100)
