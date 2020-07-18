from pathlib import Path

from curricula.grade.shortcuts import *
from curricula.grade.setup.check.common import check_file_exists
from curricula.grade.setup.build.common import build_gpp_executable

grader = Grader()


@grader.setup.check(sanity=True)
def check_build_error(submission: Submission, resources: dict):
    """Check if the program exists."""

    resources["build_error_source_path"] = submission.problem_path.joinpath("build_error.cpp")
    return check_file_exists(resources["build_error_source_path"])


@grader.setup.build(passing={"check_build_error"}, sanity=True)
def build_build_error(submission: Submission, build_error_source_path: Path):
    """Build the script."""

    result, _ = build_gpp_executable(
        source_path=build_error_source_path,
        destination_path=submission.problem_path.joinpath("build_error"))
    return result
