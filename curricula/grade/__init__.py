"""Grade is a combined library for grading C++ problem sets.

Grade is capable of testing three main aspects of C++ programs:
correctness, efficiency, and style. It includes tools for testing the
output of the code under various conditions, measuring its runtime
performance and memory usage, and running style checks.
"""

import timeit

from pathlib import Path
from typing import Iterator, Iterable, Tuple

from ..log import log
from .models import GradingAssignment, GradingProblem
from .report import AssignmentReport
from .resource import Submission, Context

root = Path(__file__).absolute().parent


class Paths:
    INCLUDE = root.joinpath("include")
    GTEST = root.joinpath("gtest")


def _run(assignment: GradingAssignment, submission_path: Path, options: dict) -> AssignmentReport:
    """Actual runtime."""

    report = AssignmentReport.create(assignment)
    context = Context(options=options)
    for problem in filter(lambda p: p.grading.is_automated, assignment.problems):
        log.debug(f"running problem {problem.short}")
        submission = Submission(
            assignment_path=submission_path,
            problem_path=submission_path.joinpath(problem.relative_path))
        report[problem.short] = problem.grader.run(context=context, submission=submission)
    return report


def run(assignment: GradingAssignment, submission_path: Path, options: dict) -> AssignmentReport:
    """Run all tests on a submission and return a dict of results."""

    log.info(f"running {submission_path}")
    start = timeit.default_timer()
    report = _run(assignment, submission_path, options)
    elapsed = timeit.default_timer() - start
    log.debug(f"finished in {round(elapsed, 5)} seconds")
    return report


def run_batch(
        assignment: GradingAssignment,
        submission_paths: Iterable[Path],
        options: dict) -> Iterator[Tuple[Path, AssignmentReport]]:
    """Run multiple reports, map directory to report."""

    # Start timer
    start = timeit.default_timer()

    for submission_path in submission_paths:
        yield submission_path, run(assignment, submission_path, options=options)

    elapsed = timeit.default_timer() - start
    log.info(f"finished batch in {round(elapsed, 5)} seconds")
