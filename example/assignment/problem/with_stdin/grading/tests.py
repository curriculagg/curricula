from pathlib import Path

from curricula.grade.shortcuts import *
from curricula.grade.setup.check.common import check_file_exists
from curricula.grade.setup.build.common import build_gpp_executable
from curricula.library import files

GPP_OPTIONS = ("-Wall", "-std=c++11")

grader = Grader()


@grader.setup.check(sanity=True)
def check_with_stdin(context: Context, resources: dict) -> CheckResult:
    """Check whether with_stdin.cpp has been submitted."""

    resources["with_stdin_source_path"] = context.problem_target_path.joinpath("with_stdin.cpp")
    return check_file_exists(resources["with_stdin_source_path"])


@grader.setup.build(dependency="check_with_stdin", sanity=True)
def build_with_stdin(with_stdin_source_path: Path, resources: dict) -> BuildResult:
    """Compile the program with gcc."""

    resources["with_stdin_path"] = Path("/tmp", "with_stdin")
    result, resources["with_stdin"] = build_gpp_executable(
        source_path=with_stdin_source_path,
        destination_path=resources["with_stdin_path"],
        gpp_options=GPP_OPTIONS)
    return result


@grader.test.correctness(dependency="build_with_stdin")
def test_with_stdin(with_stdin: ExecutableFile) -> CorrectnessResult:
    """Test a problem with stdin."""

    return CorrectnessResult(passing=with_stdin.execute(stdin=b"Hello!").stdout == b"Hello!")


@grader.teardown.cleanup(dependency="build_with_stdin")
def teardown_with_stdin(with_stdin_path: Path):
    """Delete the binary."""

    files.delete_file(with_stdin_path)
