from pathlib import Path

from curricula.grade.shortcuts import *
from curricula.grade.setup.check.common import check_file_exists
from curricula.grade.setup.build.common import build_gpp_executable

grader = Grader()


@grader.setup.build()
def check_build_error(context: Context, resources: dict):
    """Check if the program exists."""

    resources["build_error_source_path"] = context.target_path.joinpath(context.problem_short, "build_error.cpp")
    return check_file_exists(resources["build_error_source_path"])


@grader.setup.check(dependency="check_build_error")
def build_build_error(context: Context, build_error_source_path: Path):
    """Build the script."""

    result, _ = build_gpp_executable(
        source_path=build_error_source_path,
        destination_path=context.target_path.joinpath(context.problem_short, "build_error"))
    return result
