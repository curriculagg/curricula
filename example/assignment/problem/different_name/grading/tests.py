from pathlib import Path

from curricula.grade.shortcuts import *
from curricula.grade.setup.check.common import check_file_exists
from curricula.grade.setup.build.common import build_gpp_executable
from curricula.library import files

GPP_OPTIONS = ("-Wall", "-std=c++11")

grader = Grader()


@grader.setup.check(sanity=True)
def check_name_different(submission: Submission, resources: dict) -> CheckResult:
    """Check whether name_different.cpp has been submitted."""

    resources["name_different_source_path"] = submission.problem_path.joinpath("name_different.cpp")
    return check_file_exists(resources["name_different_source_path"])


@grader.setup.build(passing={"check_name_different"}, sanity=True)
def build_name_different(submission: Submission, name_different_source_path: Path, resources: dict) -> BuildResult:
    """Compile the program with gcc."""

    resources["name_different_path"] = submission.problem_path.joinpath("name_different")
    result, resources["name_different"] = build_gpp_executable(
        source_path=name_different_source_path,
        destination_path=resources["name_different_path"],
        gpp_options=GPP_OPTIONS)
    return result


@grader.test.correctness(passing={"build_name_different"})
def test_output(name_different: Executable) -> CorrectnessResult:
    """Check if the program outputs as expected."""

    runtime = name_different.execute(timeout=1)
    return CorrectnessResult(passing=runtime.stdout.strip() == b"Hello, world!", runtime=runtime.dump())


@grader.teardown.cleanup(passing={"build_name_different"})
def cleanup(name_different_path: Path):
    """Clean up executables."""

    if name_different_path.is_file():
        files.delete_file(name_different_path)
