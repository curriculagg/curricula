import json
import statistics
from typing import List, Dict, Iterable, Union, Set
from dataclasses import dataclass, field
from pathlib import Path

from ..models import GradingAssignment
from ..report import AssignmentReport
from ..task import Task


@dataclass
class TaskSummary:
    """Statistics about task results."""

    task: Task
    students_complete: List[dict] = field(default_factory=list)
    students_passing: List[dict] = field(default_factory=list)
    students_timeout: List[dict] = field(default_factory=list)


@dataclass
class StudentProblemSummary:
    """Problem results for a single student."""

    tasks_complete: List[Task] = field(default_factory=list)
    tasks_passing: List[Task] = field(default_factory=list)


@dataclass
class StudentSummary:
    """Statistics for an individual student."""

    student: dict
    problems: Dict[str, StudentProblemSummary]

    def __init__(self, student: dict, problem_shorts: Iterable[str]):
        self.student = student
        self.problems = {}
        for problem_short in problem_shorts:
            self.problems[problem_short] = StudentProblemSummary()


@dataclass
class ProblemSummary:
    """Statistics about a set of tests."""

    tasks: Dict[str, TaskSummary]
    failed_setup: Set[str]

    def __init__(self, tasks: Iterable[Task]):
        self.tasks = {task.name: TaskSummary(task) for task in tasks}
        self.failed_setup = set()


@dataclass
class Summary:
    """Overall assignment statistics."""

    problems: Dict[str, ProblemSummary]
    students: Dict[str, StudentSummary]
    failed_setup: Set[str]

    def __init__(self, assignment: GradingAssignment, students: dict):
        """Generate skeleton of data store."""

        self.problems = {}
        for problem in assignment.problems:
            if problem.grading.is_automated:
                self.problems[problem.short] = ProblemSummary(problem.grader.tasks)
        self.students = {}
        problem_shorts = tuple(self.problems.keys())
        for student_username, student in students.items():
            self.students[student_username] = StudentSummary(student, problem_shorts)
        self.failed_setup = set()


def build_student_summary(summary: Summary, assignment: GradingAssignment, report_path: Path):
    """Build a table of results with axes students and tasks."""

    report_name = report_path.parts[-1].rsplit(".")[0]
    student_summary = summary.students[report_name]

    with open(report_path) as file:
        report = AssignmentReport.load(json.load(file), assignment)

    for problem_short, problem_report in report.problems.items():
        problem_summary = summary.problems[problem_short]

        for task_name, result in problem_report.results.items():
            task_summary = problem_summary.tasks[task_name]
            task = task_summary.task
            if task.stage == "setup" and not result.passing:
                summary.failed_setup.add(report_name)
                problem_summary.failed_setup.add(report_name)

            if result.complete:
                task_summary.students_complete.append(student_summary.student)
                student_summary.problems[problem_short].tasks_complete.append(task)
            if result.passing:
                task_summary.students_passing.append(student_summary.student)
                student_summary.problems[problem_short].tasks_passing.append(task)
            if "runtime" in result.details and result.details["runtime"] is not None:
                if result.details["runtime"]["timed_out"]:
                    task_summary.students_timeout.append(student_summary.student)

    return student_summary


def build_summary(assignment: GradingAssignment, report_paths: Iterable[Path]) -> Summary:
    """Compile problem summaries."""

    students = {}
    for report_path in report_paths:
        student_username = report_path.parts[-1].rsplit(".")[0]
        students[student_username] = dict(username=student_username)
    summary = Summary(assignment, students)
    for report_path in report_paths:
        build_student_summary(summary, assignment, report_path)
    return summary


def percent(x: Union[int, float], n: int = 1) -> str:
    return f"{round(x / n * 1000) / 10 if n != 0 else 0}%"


def filter_tests(tasks: List[Task]) -> List[Task]:
    return [task for task in tasks if task.stage == "test"]


def summarize(grading_path: Path, report_paths: Iterable[Path]):
    """Do summaries of the reports in a directory."""

    assignment = GradingAssignment.read(grading_path)
    summary = build_summary(assignment, report_paths)

    for problem_short, problem_summary in summary.problems.items():
        print(f"Problem: {problem_short}")

        print("  Tests")
        for task_name, task_summary in problem_summary.tasks.items():
            print(f"    {task_name}: {len(task_summary.students_passing)}/{len(task_summary.students_complete)}",
                  f"({len(task_summary.students_timeout)} timeout)")

        scores = []
        for student_username, student_summary in summary.students.items():
            count_tests_complete = len(filter_tests(student_summary.problems[problem_short].tasks_complete))
            if count_tests_complete:
                count_tests_passing = len(filter_tests(student_summary.problems[problem_short].tasks_passing))
                scores.append(count_tests_passing / count_tests_complete)
                # print(student_username, 100 * count_tests_passing / count_tests_complete)

        print("  Statistics")
        print(f"    Total scores: {len(scores)}")
        print(f"    Mean: {percent(statistics.mean(scores)) if len(scores) > 0 else '-'}")
        print(f"    Median: {percent(statistics.median(scores)) if len(scores) > 0 else '-'}")
        print(f"    Perfect: {percent(len(list(filter(lambda x: x == 1, scores))), len(scores))}")
        print(f"    Zeros: {percent(len(list(filter(lambda x: x == 0, scores))), len(scores))}")
        print(f"    Failed setup: {len(problem_summary.failed_setup)}")

    print(f"Total submissions that failed setup: {len(summary.failed_setup)}")
    for report_name in summary.failed_setup:
        print(f"  {report_name}")
