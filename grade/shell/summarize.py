import os
import json
import statistics
import itertools
from typing import List
from dataclasses import dataclass, field
from pathlib import Path

from ..grader import Grader


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
class OverallSummary:
    """Statistics about a set of tests."""

    tasks: List[TaskSummary] = field(default_factory=list)
    students: List[StudentSummary] = field(default_factory=list)


def build_summary(grader: Grader, reports_directory: Path) -> OverallSummary:
    """Build a table of results with axes students and tasks."""

    summary = OverallSummary()
    report_names = os.listdir(str(reports_directory))
    task_lookup = {}

    for task in itertools.chain(grader.setups, grader.tests, grader.teardowns):
        task_summary = TaskSummary(task.dump())
        task_lookup[task_summary.task["name"]] = task_summary
        summary.tasks.append(task_summary)

    for report_name in report_names:
        with reports_directory.joinpath(report_name).open() as file:
            report = json.load(file)

        student = StudentSummary(dict(username=report_name.split(".")[0]))
        summary.students.append(student)

        for task_result in report:
            task_name = task_result["task"]["name"]
            task = task_lookup[task_name]

            if task_result["complete"]:
                task.students_complete.append(student)
                student.tasks_complete.append(task)
            if task_result["passed"]:
                task.students_passed.append(student)
                student.tasks_passed.append(task)

    return summary


def percent(x, n) -> str:
    return f"{round(x / n * 1000) / 10}%"


def filter_tests(tasks: List[TaskSummary]) -> List[TaskSummary]:
    return list(task_summary for task_summary in tasks if task_summary.task["kind"] == "test")


def summarize(grader: Grader, args: dict):
    """Do summaries of the reports in a directory."""

    reports_directory = Path(args.pop("reports"))
    summary = build_summary(grader, reports_directory)

    for task_summary in summary.tasks:
        task_name = task_summary.task["name"]
        print(f"{task_name}: {percent(len(task_summary.students_passed), len(task_summary.students_complete))}")

#
#
# def p(x, n):
#     return f"{round(x / n * 100)}%"
#
#
# def pd(x, n):
#     return f"{round(x / n * 100)}%, -{n - x}"
#
#
# print(f"Total: {overall.total}")
# print(f"Setup: {overall.setup} ({pd(overall.setup, overall.total)})")
# print(f"Average: {p(statistics.mean(overall.passed), 1)}")
# for task_name, summary in tasks.items():
#     print(f"{task_name}:")
#     print(f"  Complete: {summary.complete} ({pd(summary.complete, overall.total)})")
#     print(f"  Passed: {summary.passed} ({pd(summary.passed, overall.total)})")
